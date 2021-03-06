import subprocess
import os
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


def elasticsearch():
    if os.environ.get('ES_URL') is None:
        os.environ['ES_PORT'] = '9200'
        os.environ['ES_HOST'] = 'elasticsearch'
        os.environ['ES_NAME'] = 'elasticsearch'
        os.environ['ES_URL'] = "http://elasticsearch:{}".format(
            os.environ['ES_PORT'])
        set_version('ES_VERSION', "6.3.0", "snapshot")
        start("docker/elasticsearch/start.sh")
    else:
        parsed_url = urlparse(os.environ['ES_URL'])
        os.environ['ES_PORT'] = str(parsed_url.port)
        os.environ['ES_HOST'] = parsed_url.hostname
    return os.environ['ES_URL']


def kibana():
    if os.environ.get('KIBANA_URL') is None:
        os.environ['KIBANA_PORT'] = "5601"
        os.environ['KIBANA_HOST'] = 'kibana'
        os.environ['KIBANA_URL'] = "http://kibana:{}".format(
            os.environ['KIBANA_PORT'])
        set_version('KIBANA_VERSION', "6.3.0", "snapshot")
        start("docker/kibana/start.sh")
    return os.environ['KIBANA_URL']


def apm_server():
    if os.environ.get('APM_SERVER_URL') is None:
        name = os.environ['APM_SERVER_NAME'] = 'apmserver'
        port = os.environ['APM_SERVER_PORT'] = "8200"
        os.environ['APM_SERVER_URL'] = "http://{}:{}".format(name, port)
        set_version('APM_SERVER_VERSION')
        start("docker/apm_server/start.sh")
    return "{}/healthcheck".format(os.environ['APM_SERVER_URL'])


def flask():
    os.environ['FLASK_SERVICE_NAME'] = "flaskapp"
    os.environ['FLASK_PORT'] = "8001"
    os.environ['FLASK_URL'] = "http://{}:{}".format(os.environ['FLASK_SERVICE_NAME'],
                                                    os.environ['FLASK_PORT'])
    start("docker/python/flask/start.sh")
    return "{}/healthcheck".format(os.environ['FLASK_URL'])


def django():
    os.environ['DJANGO_SERVICE_NAME'] = "djangoapp"
    os.environ['DJANGO_PORT'] = "8003"
    os.environ['DJANGO_URL'] = "http://{}:{}".format(os.environ['DJANGO_SERVICE_NAME'],
                                                     os.environ['DJANGO_PORT'])
    start("docker/python/django/start.sh")
    return "{}/healthcheck".format(os.environ['DJANGO_URL'])


def express():
    os.environ['EXPRESS_APP_NAME'] = "expressapp"
    os.environ['EXPRESS_PORT'] = "8010"
    os.environ['EXPRESS_URL'] = "http://{}:{}".format(os.environ['EXPRESS_APP_NAME'],
                                                      os.environ['EXPRESS_PORT'])
    start("docker/nodejs/express/start.sh")
    return "{}/healthcheck".format(os.environ['EXPRESS_URL'])


def rails():
    set_version('RUBY_AGENT_VERSION')
    os.environ['RAILS_SERVICE_NAME'] = "railsapp"
    os.environ['RAILS_PORT'] = "8020"
    os.environ['RAILS_URL'] = "http://{}:{}".format(os.environ['RAILS_SERVICE_NAME'],
                                                     os.environ['RAILS_PORT'])
    start("docker/ruby/rails/start.sh")
    return "{}/healthcheck".format(os.environ['RAILS_URL'])


def go_nethttp():
    service_name = "go_nethttp"
    url = "http://{}:8080".format(service_name)
    os.environ['GO_NETHTTP_SERVICE_NAME'] = service_name
    os.environ['GO_NETHTTP_URL'] = url
    start("docker/go/nethttp/start.sh")
    return url + "/healthcheck"


def python_agents():
    set_version('PYTHON_AGENT_VERSION')
    return [flask(), django()]


def nodejs_agents():
    set_version('NODEJS_AGENT_VERSION')
    return [express()]


def ruby_agents():
    return [rails()]


def go_agents():
    return [go_nethttp()]


def prepare():
    if os.environ.get("NETWORK") is None:
        os.environ["NETWORK"] = "apm_testing"
    if 'REUSE_CONTAINERS' not in os.environ:
        start("docker/prepare_docker.sh")


def start(script):
    if 'REUSE_CONTAINERS' in os.environ:
        print("Reusing started containers...")
    else:
        subprocess.check_call([script])


def set_version(env_var, default='master', state="github"):
    v = os.environ.get(env_var)
    env_var_state = "{}_STATE".format(env_var)
    if v is None or v == "":
        os.environ[env_var_state] = state
        os.environ[env_var] = default
    else:
        parts = v.split(";")
        if len(parts) == 1:
            os.environ[env_var_state] = state
            os.environ[env_var] = parts[0]
        elif len(parts) == 2:
            os.environ[env_var_state] = parts[0]
            os.environ[env_var] = parts[1]
        else:
            raise Exception("Invalid Version {}".format(v))


if __name__ == '__main__':
    prepare()
    urls = [elasticsearch(), apm_server()]

    agents = os.environ.get("AGENTS")
    if agents is not None:
        for agent in agents.split(','):
            if agent == "python":
                urls += python_agents()
            elif agent == "nodejs":
                urls += nodejs_agents()
            elif agent == "ruby":
                urls += ruby_agents()
            elif agent == "go":
                urls += go_agents()
            else:
                raise Exception("Agent {} not supported".format(agent))

    if "TEST_KIBANA" in os.environ:
        urls.append(kibana())

    os.environ['URLS'] = ",".join(urls)
    subprocess.check_call(["docker/run_tests.sh"])
