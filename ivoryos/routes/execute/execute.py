import csv
import os
import time
import importlib

from flask import Blueprint, redirect, url_for, flash, jsonify, request, render_template, session, \
    current_app, g, send_file
from flask_login import login_required

from ivoryos.routes.execute.execute_file import files
from ivoryos.utils import utils
from ivoryos.utils.bo_campaign import parse_optimization_form
from ivoryos.utils.db_models import SingleStep, WorkflowRun, WorkflowStep, WorkflowPhase
from ivoryos.utils.global_config import GlobalConfig
from ivoryos.utils.form import create_action_button
from werkzeug.utils import secure_filename
from ivoryos.socket_handlers import runner, retry, pause, abort_pending, abort_current

execute = Blueprint('execute', __name__, template_folder='templates')
execute.register_blueprint(files)
global_config = GlobalConfig()

@execute.route("/executions/config", methods=['GET', 'POST'])
@login_required
def experiment_run():
    deck = global_config.deck
    script = utils.get_script_file()
    existing_data = None
    off_line = current_app.config["OFF_LINE"]
    deck_list = utils.import_history(os.path.join(current_app.config["OUTPUT_FOLDER"], 'deck_history.txt'))
    optimizers_schema = {k: v.get_schema() for k, v in global_config.optimizers.items()}
    design_buttons = {stype: create_action_button(script, stype) for stype in script.stypes}
    config_preview = []
    config_file_list = [i for i in os.listdir(current_app.config["CSV_FOLDER"]) if not i == ".gitkeep"]

    try:
        snapshot = global_config.deck_snapshot
        exec_string = script.python_script if script.python_script else script.compile(
            current_app.config['SCRIPT_FOLDER'], snapshot=snapshot)
    except Exception as e:
        flash(e.__str__())
        if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
            return jsonify({"error": e.__str__()})
        else:
            return redirect(url_for("design.experiment_builder"))

    config_file = request.args.get("filename")
    config = []
    if "filename" in request.args:
        session['config_file'] = config_file
    filename = session.get("config_file")
    if filename:
        config = list(csv.DictReader(open(os.path.join(current_app.config['CSV_FOLDER'], filename))))
        config_preview = config[1:]
        arg_type = config.pop(0)

    try:
        if isinstance(exec_string, dict):
            for key, func_str in exec_string.items():
                compile(func_str, f'<function_{key}>', 'exec')
        else:
            if isinstance(exec_string, str):
                compile(exec_string, '<script>', 'exec')
            line_collection = {}
    except Exception as e:
        g.logger.exception(f"Exception while executing script: {e}")
        flash(f"Please check syntax!! {e}")
        return redirect(url_for("design.experiment_builder"))

    current_lines_script = script
    if runner.current_task and runner.current_task.get("script"):
        current_lines_script = runner.current_task["script"]
        
    line_collection = current_lines_script.render_nested_script_lines(current_lines_script.script_dict, snapshot=snapshot)
    run_name = script.name if script.name else "untitled"
    dismiss = session.get("dismiss", None)
    no_deck_warning = False
    _, return_list = script.config_return()
    config_list, config_type_list = script.config("script")

    for key, type_str in config_type_list.items():
        if isinstance(type_str, list):
             enum_entries = [t for t in type_str if isinstance(t, str) and t.startswith("Enum:")]
             if enum_entries:
                 type_str = enum_entries[0]
        
        if isinstance(type_str, str) and type_str.startswith("Enum:"):
            try:
                _, full_path = type_str.split(":", 1)
                module_name, class_name = full_path.rsplit(".", 1)
                mod = importlib.import_module(module_name)
                enum_class = getattr(mod, class_name)
                options = [e.name for e in enum_class]
                config_type_list[key] = f"Enum:{','.join(options)}"
            except Exception:
                pass

    # ---> EL FILTRO MAGICO PARA LA WEB: Ignorará la carpeta de "basura" <---
    data_list = []
    for root, dirs, files_in_dir in os.walk(current_app.config['DATA_FOLDER']):
        for f in files_in_dir:
            if f.endswith('.csv') and f != ".gitkeep":
                # Condición de oro: si la ruta tiene "logs", NO la mostramos
                if "logs" not in root.split(os.sep):
                    rel_path = os.path.relpath(os.path.join(root, f), current_app.config['DATA_FOLDER'])
                    data_list.append(rel_path.replace('\\', '/'))
    data_list.sort(key=lambda f: os.path.getctime(os.path.join(current_app.config['DATA_FOLDER'], f)), reverse=True)

    if deck is None:
        no_deck_warning = True
    elif script.deck:
        is_deck_match = script.deck == deck.__name__ or script.deck == os.path.splitext(os.path.basename(deck.__file__))[0]
        if not is_deck_match:
            flash(f"This script is not compatible with current deck, import {script.deck}")

    if request.method == "POST":
        compiled = False
        if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
            payload_json = request.get_json()
            compiled = True
            if "kwargs" in payload_json:
                config = payload_json["kwargs"]
            repeat = payload_json.pop("repeat", None)
            batch_size = payload_json.pop('batch_size', 1)
        else:
            display_name = request.form.get("display_name")
            if "bo" in request.form:
                bo_args = request.form.to_dict()
                existing_data = bo_args.pop("existing_data")
                bo_args.pop("display_name", None)
            if "online-config" in request.form:
                config_args = request.form.to_dict()
                config_args.pop("batch_size", None)
                config_args.pop("display_name", None)
                config = utils.web_config_entry_wrapper(config_args, config_list)
            batch_size = int(request.form.get('batch_size', 1))
            repeat = request.form.get('repeat', None)

        try:
            base_datapath = current_app.config["DATA_FOLDER"]
            run_name = script.validate_function_name(run_name)
            
            # 1. Crear carpeta principal para la gráfica y tus datos reales
            timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
            datapath = os.path.join(base_datapath, f"{run_name}_{timestamp}")
            os.makedirs(datapath, exist_ok=True) 
            
            # 2. Crear subcarpeta para tirar la "basura" de IvoryOS
            log_path = os.path.join(datapath, "logs")
            os.makedirs(log_path, exist_ok=True)
            
            socketio_instance = g.socketio
            def on_start_callback():
                snapshot = global_config.deck_snapshot
                line_collection = script.render_nested_script_lines(script.script_dict, snapshot=snapshot)
                progress_panel_html = render_template('components/progress_panel.html', line_collection=line_collection)
                socketio_instance.emit('start_task', {
                    'run_name': run_name,
                    'progress_panel_html': progress_panel_html
                })

            # 3. Le decimos a IvoryOS que guarde su archivo inútil en 'log_path'
            result = runner.run_script(script=script, run_name=run_name, config=config,
                              logger=g.logger, socketio=g.socketio, repeat_count=repeat,
                              output_path=log_path, compiled=compiled, history=existing_data,
                              current_app=current_app._get_current_object(), batch_size=batch_size,
                              on_start=on_start_callback, display_name=display_name
                              )

            if utils.check_config_duplicate(config):
                flash(f"WARNING: Duplicate in config entries.")
        except Exception as e:
            if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
                return jsonify({"error": e.__str__()})
            else:
                flash(e)

    if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
        while not global_config.runner_status:
            time.sleep(1)
        return jsonify({"status": "task started", "task_id": global_config.runner_status.get("id")})
    else:
        return render_template('experiment_run.html', script=script.script_dict, filename=filename,
                               dot_py=exec_string, line_collection=line_collection,
                               return_list=return_list, config_list=config_list, config_file_list=config_file_list,
                               config_preview=config_preview, data_list=data_list, config_type_list=config_type_list,
                               no_deck_warning=no_deck_warning, dismiss=dismiss, design_buttons=design_buttons,
                               history=deck_list, pause_status=runner.pause_status(), optimizer_schema=optimizers_schema)

@execute.route("/executions/optimizer_schema", methods=["POST"])
def optimizer_schema():
    if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
        payload_json = request.get_json()
        optimizer_type = payload_json.pop("optimizer_type", None)
        if optimizer_type:
            _schema = global_config.optimizers.get(optimizer_type, None)
            if _schema is None:
                return jsonify({"error": f"Optimizer {optimizer_type} is not supported or not found."})
            return jsonify(_schema.get_schema())
        else:
            optimizers_schema = {k: v.get_schema() for k, v in global_config.optimizers.items()}
            return jsonify(optimizers_schema)
    return None

@execute.route("/executions/campaign", methods=["POST"])
@login_required
def run_bo():
    script = utils.get_script_file()
    run_name = script.name if script.name else "untitled"

    if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
        payload_json = request.get_json()
        objectives = payload_json.pop("objectives", None)
        parameters = payload_json.pop("parameters", None)
        steps = payload_json.pop("steps", None)
        constraints = payload_json.pop("parameter_constraints", None)
        repeat = payload_json.pop("repeat", None)
        batch_size = payload_json.pop("batch_size", None)
        optimizer_type = payload_json.pop("optimizer_type", None)
        existing_data = payload_json.pop("existing_data", None)
        additional_params = payload_json.pop("additional_params", None)
    else:
        payload = request.form.to_dict()
        repeat = payload.pop("repeat", None)
        optimizer_type = payload.pop("optimizer_type", None)
        existing_data = payload.pop("existing_data", None)
        upload_new_data = payload.pop("data_mode_toggle", None)

        if upload_new_data == 'on':
            uploaded_file = request.files.get("uploaded_data")
            if uploaded_file and uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                filepath = os.path.join(current_app.config['DATA_FOLDER'], filename)
                uploaded_file.save(filepath)
                existing_data = filename
            else:
                existing_data = ''
        else:
            existing_data = existing_data

        batch_mode = payload.pop("batch_mode", None)
        batch_size = payload.pop("batch_size", 1)

        constraint_exprs = request.form.getlist("constraint_expr")
        constraints = [expr.strip() for expr in constraint_exprs if expr.strip()]

        for key in list(payload.keys()):
            if key.startswith("constraint_expr"):
                payload.pop(key, None)

        parameters, objectives, steps, additional_params = parse_optimization_form(payload)

    try:
        base_datapath = current_app.config["DATA_FOLDER"]
        run_name = script.validate_function_name(run_name)
        
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        datapath = os.path.join(base_datapath, f"{run_name}_{timestamp}")
        os.makedirs(datapath, exist_ok=True)

        log_path = os.path.join(datapath, "logs")
        os.makedirs(log_path, exist_ok=True)

        Optimizer = global_config.optimizers.get(optimizer_type, None)
        if not Optimizer:
            raise ValueError(f"Optimizer {optimizer_type} is not supported or not found.")

        socketio_instance = g.socketio
        def on_start_callback():
            snapshot = global_config.deck_snapshot
            line_collection = script.render_nested_script_lines(script.script_dict, snapshot=snapshot)
            progress_panel_html = render_template('components/progress_panel.html', line_collection=line_collection)
            socketio_instance.emit('start_task', {
                'run_name': run_name,
                'progress_panel_html': progress_panel_html
            })

        result = runner.run_script(script=script, run_name=run_name, optimizer=None,
                          logger=g.logger, socketio=g.socketio, repeat_count=repeat,
                          output_path=log_path, compiled=False, history=existing_data,
                          current_app=current_app._get_current_object(), batch_size=int(batch_size),
                          objectives=objectives, parameters=parameters, constraints=constraints, steps=steps,
                          optimizer_cls=Optimizer, additional_params=additional_params,
                          on_start=on_start_callback
                          )
        if result == "queued":
            flash(f"System busy. Optimization {run_name} added to queue.")
        else:
            flash(f"Optimization {run_name} started.")

    except Exception as e:
        if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
            return jsonify({"error": e.__str__()})
        else:
            flash(e.__str__())
    return redirect(url_for("execute.experiment_run"))

@execute.route("/executions/latest_plot")
@login_required
def get_optimizer_plot():
    optimizer = current_app.config.get("LAST_OPTIMIZER")
    if optimizer is not None:
        latest_file = optimizer.get_plots('placeholder')
        if files:
            return send_file(latest_file, mimetype="image/png")
    return jsonify({"error": "No plots found"}), 404

@execute.route("/executions/queue", methods=["GET"])
@login_required
def get_queue():
    return jsonify(runner.get_queue_status())

@execute.route("/executions/queue/delete", methods=["POST"])
@login_required
def delete_queue_task():
    try:
        data = request.get_json()
        task_id = data.get("id")
        if runner.remove_task(task_id):
            return jsonify({"status": "ok"})
        return jsonify({"error": "Failed to remove task"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@execute.route("/executions/queue/reorder", methods=["POST"])
@login_required
def reorder_queue_task():
    try:
        data = request.get_json()
        task_id = data.get("id")
        direction = data.get("direction")
        if runner.reorder_tasks(task_id, direction):
            return jsonify({"status": "ok"})
        return jsonify({"error": "Failed to reorder task"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@execute.route("/executions/queue/task/<int:task_id>", methods=["GET"])
@login_required
def get_queue_task_details(task_id):
    details = runner.get_task_details(task_id)
    if details:
        return jsonify(details)
    return jsonify({"error": "Task not found"}), 404

@execute.route("/executions/status", methods=["GET"])
def runner_status():
    runner_busy = global_config.runner_lock.locked()
    status = {"busy": runner_busy}
    task_status = global_config.runner_status
    current_step = {}

    if task_status is not None:
        task_type = task_status["type"]
        task_id = task_status["id"]
        if task_type == "task":
            step = SingleStep.query.get(task_id)
            current_step = step.as_dict()
        if task_type == "workflow":
            workflow = WorkflowRun.query.get(task_id)
            if workflow is not None:
                phases = WorkflowPhase.query.filter_by(run_id=workflow.id).order_by(WorkflowPhase.start_time).all()
                current_phase = phases[-1]
                latest_step = WorkflowStep.query.filter_by(phase_id=current_phase.id).order_by(
                    WorkflowStep.start_time.desc()).first()
                if latest_step is not None:
                    current_step = latest_step.as_dict()
                status["workflow_status"] = {"workflow_info": workflow.as_dict(), "runner_status": runner.get_status()}
    status["current_task"] = current_step
    return jsonify(status), 200

@execute.route("/executions/abort/next-iteration", methods=["POST"])
def api_abort_pending():
    abort_pending()
    return jsonify({"status": "ok"}), 200

@execute.route("/executions/abort/next-task", methods=["POST"])
def api_abort_current():
    abort_current()
    return jsonify({"status": "ok"}), 200

@execute.route("/executions/pause-resume", methods=["POST"])
def api_pause():
    msg = pause()
    return jsonify({"status": "ok", "pause_status": msg}), 200

@execute.route("/executions/retry", methods=["POST"])
def api_retry():
    retry()
    return jsonify({"status": "ok, retrying failed step"}), 200

@execute.route('/files/preview/<path:filename>')
@login_required
def data_preview(filename):
    import csv
    import os
    from flask import abort

    data_folder = current_app.config['DATA_FOLDER']
    file_path = os.path.join(data_folder, filename)
    if not os.path.exists(file_path):
        abort(404)
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    return jsonify({"columns": reader.fieldnames, "rows": rows})