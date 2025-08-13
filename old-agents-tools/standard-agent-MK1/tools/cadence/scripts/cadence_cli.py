import requests
import json
import sys

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No JSON parameters provided."}))
        sys.exit(1)

    params = json.loads(sys.argv[1])
    operation = params.get('operation')
    server_url = params.get('server_url', 'http://localhost:8334').rstrip('/')
    workflow_name = params.get('workflow_name')
    inputs = params.get('inputs', {})
    run_id = params.get('run_id')

    endpoint = ""
    method = "GET"
    payload = None

    try:
        if operation == 'list_workflows':
            endpoint = '/api/v1/workflows'
        elif operation == 'get_workflow' and workflow_name:
            endpoint = f'/api/v1/workflows/{workflow_name}'
        elif operation == 'trigger' and workflow_name:
            endpoint = f'/api/v1/workflows/{workflow_name}/trigger'
            method = "POST"
            payload = inputs
        elif operation == 'get_runs':
            endpoint = '/api/v1/runs'
        elif operation == 'get_run_details' and run_id:
            endpoint = f'/api/v1/runs/{run_id}'
        else:
            raise ValueError(f"Invalid operation or missing parameters for '{operation}'")

        response = requests.request(method, f"{server_url}{endpoint}", json=payload, timeout=30)
        response.raise_for_status()
        print(json.dumps({"success": True, "result": response.json()}))

    except requests.exceptions.RequestException as e:
        print(json.dumps({"success": False, "error": f"API request failed: {e}"}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    main()
