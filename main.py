from bottle import post, run, request
import argparse

from requests import get


def parse_args():
    parser = argparse.ArgumentParser(description='Write task logs from Octopus to disk.')
    parser.add_argument('--octopusUrl', dest='octopus_url', action='store', help='The Octopus server URL.',
                        required=True)
    parser.add_argument('--octopusApiKey', dest='octopus_api_key', action='store', help='The Octopus API key',
                        required=True)

    return parser.parse_args()


def build_headers():
    return {"X-Octopus-ApiKey": args.octopus_api_key}


@post('/')
def webhook():
    deployment_id = extract_deployment_id(request.json)
    space_id = extract_space_id(request.json)
    task_id = get_task_id(space_id, deployment_id)
    task_log = get_task_log(space_id, task_id)

    with open(task_id + ".log", "w") as outfile:
        outfile.write(task_log)


def extract_deployment_id(message):
    deployment_ids = [a["ReferencedDocumentId"] for a in message["Payload"]["Event"]["MessageReferences"] if
                  a["ReferencedDocumentId"].startswith("Deployments-")]

    if len(deployment_ids) == 1:
        return deployment_ids[0]

    raise "Failed to find deployment ID in webhook message"


def extract_space_id(message):
    return message["Payload"]["Event"]["SpaceId"]


def get_task_id(space_id, deployment_id):
    deployment_url = args.octopus_url + "/api/" + space_id + "/deployments/" + deployment_id
    response = get(deployment_url, headers=headers)
    deployment_json = response.json()
    return deployment_json["TaskId"]


def get_task_log(space_id, task_id):
    return get(args.octopus_url + "/api/" + space_id + "/tasks/" + task_id + "/raw",
                   headers=headers).text


args = parse_args()
headers = build_headers()
run(host='localhost', port=8080, debug=True)
