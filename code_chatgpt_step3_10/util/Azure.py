from azure.ai.ml import MLClient
from azure.identity import (
    DefaultAzureCredential,
    InteractiveBrowserCredential,
    ClientSecretCredential
)
from azure.ai.ml.entities import (
    AmlCompute,
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    OnlineRequestSettings,
    ProbeSettings
)
import json
import time
import sys
import os

# PATH = os.path.join(os.path.abspath('.'), 'llama2-7b_output')
# FILE_PATH1 = os.path.join(PATH, "step1_findState.txt") #"step1_findState(in-context).txt")
# FILE_PATH2 = os.path.join(PATH, "step2_genInputs.txt") #"step2_genInputs(in-context).txt")
# FILE_PATH3 = os.path.join(PATH, "step3_selectInput.txt") # "step3_selectInput(in-context+cot).txt"
SUBSCRIPTION_ID="70210d86-6643-4dc3-baa4-27110e157597"
RESOURCE_GROUP_NAME="Gavin"
WORKSPACE_NAME="Llama2-7b"
REGISTRY = "azureml-meta" #"azureml"
MODEL_NAME = "Llama-2-13b" #"gpt2"
VM_NAME = "Standard_NC24s_v3" #"Standard_DS2_v2"
ENDPOINT_NAME = "llama2-7b-endpoint"
DEPLOYMENT_NAME = "llama2-7b-deployment"


def set_up_pre():
    try:
        credential = DefaultAzureCredential()
        # credential = ClientSecretCredential("1bdb7bb8-82ad-4b79-bad5-22899ae910db", "7b285d5a-6fe2-41dd-b4ff-e49401f16e92", "Wxf8Q~am7AHD7diBFKcwzftLIhmJFGqKJp4.lb~o")
        credential.get_token("https://management.azure.com/.default")
    except Exception as ex:
        credential = InteractiveBrowserCredential()

    workspace_ml_client = MLClient(
        credential,
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP_NAME,
        workspace_name=WORKSPACE_NAME,
    )
    registry_ml_client = MLClient(credential, registry_name=REGISTRY)
    return workspace_ml_client

def pick_model(registry_ml_client): #Llama-2-13b 
    version_list = list(registry_ml_client.models.list(MODEL_NAME))
    if len(version_list) == 0:
        print("Model not found in registry")
        sys.exit(-1)
    else:
        model_version = version_list[0].version
        foundation_model = registry_ml_client.models.get(MODEL_NAME, model_version)
        print(
            "\n\nUsing model name: {0}, version: {1}, id: {2} for inferencing".format(
                foundation_model.name, foundation_model.version, foundation_model.id
            )
        )
        return foundation_model

def create_endpoint(workspace_ml_client):
    try:
        endpoint = workspace_ml_client.online_endpoints.get(ENDPOINT_NAME)
        print("---Endpoint already exists---")
    except:
        # Create an online endpoint if it doesn't exist
        # Define the endpoint
        endpoint = ManagedOnlineEndpoint(
            name=ENDPOINT_NAME,
            description="Test endpoint for model",
            auth_mode="key",
        )

        # Trigger the endpoint creation
        try:
            workspace_ml_client.begin_create_or_update(endpoint).wait()
            print("\n---Endpoint created successfully---\n")
        except Exception as err:
            raise RuntimeError(
                f"Endpoint creation failed. Detailed Response:\n{err}"
            ) from err

def deploy(foundation_model, workspace_ml_client):
    deployment = ManagedOnlineDeployment(
        name=DEPLOYMENT_NAME,
        endpoint_name=ENDPOINT_NAME,
        model=foundation_model.id,
        instance_type=VM_NAME,
        instance_count=1,
        environment_variables={
            "SUBSCRIPTION_ID": SUBSCRIPTION_ID,
            "RESOURCE_GROUP_NAME": RESOURCE_GROUP_NAME
        },
        request_settings=OnlineRequestSettings(request_timeout_ms=90000),
        liveness_probe=ProbeSettings(
            failure_threshold=30,
            success_threshold=1,
            period=100,
            initial_delay=500,
        ),
        readiness_probe=ProbeSettings(
            failure_threshold=30,
            success_threshold=1,
            period=100,
            initial_delay=500,
        ),
    )

    # Trigger the deployment creation
    try:
        workspace_ml_client.begin_create_or_update(deployment).wait()
        print("\n---Deployment created successfully---\n")
    except Exception as err:
        delete(workspace_ml_client, ENDPOINT_NAME)
        raise RuntimeError(
            f"Deployment creation failed. Detailed Response:\n{err}"
        ) from err

def test(prompt, workspace_ml_client):
    try:
        test_json = {
            "input_data": {
                "input_string": [prompt],
                "parameters": {
                    "temperature": 0.1, 
                    "max_new_tokens": 100
                },
            }
        }
        # save the json object to a file named sample_score.json in the ./dataset folder
        with open(os.path.join(".", "dataset", "sample_score.json"), "w") as f:
            json.dump(test_json, f)
        # score the sample_score.json file using the online endpoint with the azureml endpoint invoke method
        response = workspace_ml_client.online_endpoints.invoke(
            endpoint_name=ENDPOINT_NAME,
            deployment_name=DEPLOYMENT_NAME,
            request_file="./dataset/sample_score.json",
        )
        responses = ['']
        temp = json.loads(response)
        for k, v in temp[0].items():
            index = int(k)
            responses[index] = v

        return responses[0]
    except Exception as err:
        print("Response error. Detailed information", err)
        print("failed in testing")

def delete(workspace_ml_client):
    workspace_ml_client.online_endpoints.begin_delete(DEPLOYMENT_NAME).result()
    print("success in deleting endpoint")

def run():
    workspace_ml_client = set_up_pre()
    # llama2_7b = pick_model(MODEL_NAME, registry_ml_client)
    # online_endpoint_name = create_endpoint(workspace_ml_client)
    # deployment_name = deploy(llama2_7b, online_endpoint_name, workspace_ml_client)
    # test("", workspace_ml_client)
    delete(workspace_ml_client)
    