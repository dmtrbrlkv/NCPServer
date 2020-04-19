from argparse import ArgumentParser
from notescompy import session
import logging
from flask import Flask, jsonify, request
import json


def get_config():
    ap = ArgumentParser()
    ap.add_argument("-c", "--config", action="store", default="config.json")
    ap.add_argument("-p", "--password", action="store", default="")

    options = ap.parse_args()
    with open(options.config) as cf:
        config = json.load(cf)
    if options.password:
        config["password"] = options.password
    return config

def check_method(dbname, method, databases):
    if dbname not in databases:
        return "Not available db " + dbname

    method_config = databases[dbname]["methods"]

    if method not in method_config or not method_config[method]:
        return f"{method.capitalize()} method not available"

    return ""


def get_db(dbname, databases):
    db_config = databases[dbname]
    db = session.open_database(db_config["server"], db_config["filepath"])
    if not db.is_open:
        raise RuntimeError(f"{dbname} has not been opened yet")
    return db


def get_FPF(dbname, headers, databases, separator):
    doc_info_config = databases[dbname]["doc_info"]
    if "fields" in doc_info_config and doc_info_config["fields"] and "fields" in headers:
        fields = headers["fields"]
        fields = fields.split(separator)
    else:
        fields = None

    if "properties" in doc_info_config and doc_info_config["properties"] and "properties" in headers:
        properties = headers["properties"]
        properties = properties.split(separator)
    else:
        properties = None

    if "formulas" in doc_info_config and doc_info_config["formulas"] and "formulas" in headers:
        formulas = headers["formulas"]
        formulas = formulas.split(separator)
    else:
        formulas = None

    return fields, properties, formulas


def init():
    config = get_config()
    if config["global_session"]:
        s = session.Session(config["password"])
    base_url = config["url"]
    databases = config["databases"]
    separator = config["separator"]
    app = Flask(__name__)
    if "debug" in config and config["debug"]:
        app.debug = True

    if "port" not in config:
        config["port"] = 8080

    logging.basicConfig(filename=config["log"], level=logging.INFO if not config["debug"] else logging.DEBUG,
                        format=config["log_format"], datefmt=config["log_date"])

    if "password" in config:
        del config["password"]
    return app, config, base_url, databases, separator


def create_routs(base_url, app, databases, separator):
    @app.route(base_url + '/')
    def index():
        return_databases = {}
        for dbname, config in databases.items():
            return_config = {}

            method_config = databases[dbname]["methods"]
            doc_info_config = databases[dbname]["doc_info"]

            if "view" in method_config:
                method_config["view"] = [v for v in method_config["view"]]

            return_config["methods"] = method_config
            return_config["doc_info"] = doc_info_config

            return_databases[dbname] = return_config

        return jsonify(return_databases)

    @app.route(base_url + '/<dbname>/view/<viewname>')
    def view(dbname, viewname):
        check = check_method(dbname, "view", databases)

        if check:
            return check, 403

        view_config = databases[dbname]["methods"]["view"]
        if viewname not in view_config:
            return f"Not available view {viewname}", 403

        try:
            db = get_db(dbname, databases)
        except:
            app.logger.exception(dbname)
            return f"Database {dbname} temporary not available", 500

        view = db.get_view(view_config[viewname])
        if not view:
            app.logger.error(f"View {view_config[viewname]} from {db} not available")
            return f"View {viewname} temporary not available", 500

        if "keys" in request.headers:
            keys = request.headers["keys"]
            keys = keys.split(separator)
        else:
            keys = None

        fields, properties, formulas = get_FPF(dbname, request.headers, databases, separator)

        if keys:
            try:
                col = view.get_all_documents_by_key(keys)
            except:
                app.logger.exception(" * Bad request")
                return f"Bad request, check keys", 400
            data = col.get_values(fields=fields, properties=properties, formulas=formulas)
        else:
            data = view.get_values()

        return jsonify(data)

    @app.route(base_url + '/<dbname>/search')
    def search(dbname):
        check = check_method(dbname, "search", databases)

        if check:
            return check, 403

        if "search_formula" in request.headers:
            search_formula = request.headers["search_formula"]
        else:
            return f"Bad request, search formula not specified", 400

        try:
            db = get_db(dbname, databases)
        except:
            app.logger.exception(dbname)
            return f"Database {dbname} temporary not available", 500

        try:
            col = db.search(search_formula)
        except:
            app.logger.exception(" * Bad request")
            return f"Bad request, check search formula", 400

        fields, properties, formulas = get_FPF(dbname, request.headers, databases, separator)

        try:
            data = col.get_values(fields=fields, properties=properties, formulas=formulas)
            return jsonify(data)
        except:
            app.logger.exception(" * Bad request")
            return f"Bad request, check properties and formulas", 400

    @app.route(base_url + '/<dbname>/document/<doc_id>')
    def document(dbname, doc_id):
        check = check_method(dbname, "document", databases)

        if check:
            return check, 403

        try:
            db = get_db(dbname, databases)
        except:
            app.logger.exception(dbname)
            return f"Database {dbname} temporary not available", 500

        doc = db.get_document_by_unid(doc_id)

        if doc:
            fields, properties, formulas = get_FPF(dbname, request.headers, databases, separator)

            try:
                data = doc.get_values(fields=fields, properties=properties, formulas=formulas)
                return jsonify(data)
            except:
                app.logger.exception(" * Bad request")
                return f"Bad request, check properties and formulas", 400

        return f"Document {doc_id} not available", 404

    @app.route(base_url + '/<dbname>')
    def db_info(dbname):
        if dbname not in databases:
            return "Not available db " + dbname

        try:
            db = get_db(dbname, databases)
        except:
            app.logger.exception(dbname)
            return f"Database {dbname} temporary not available", 500

        res = {"Documents": db.all_documents.count, "Size": db.size}
        return jsonify(res)
