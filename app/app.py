import utils

def main():
    app, config, base_url, databases, separator = utils.init()
    app.logger.info(f"Start with config: {config}")
    utils.create_routs(base_url, app, databases, separator)
    app.run(port=config["port"])


if __name__ == '__main__':
    main()