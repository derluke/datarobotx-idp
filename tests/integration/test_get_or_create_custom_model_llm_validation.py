# mypy: ignore-errors
import pathlib

import pytest

from datarobotx.idp.custom_model_llm_validation import (
    get_or_create_custom_model_llm_validation,
)
from datarobotx.idp.custom_model_versions import get_or_create_custom_model_version
from datarobotx.idp.custom_models import get_or_create_custom_model
from datarobotx.idp.deployments import (
    get_or_create_deployment_from_registered_model_version,
)
from datarobotx.idp.registered_model_versions import (
    get_or_create_registered_custom_model_version,
)


@pytest.fixture
def custom_model_dir(tmp_path):
    model_dir = tmp_path / "custom_model_llm_validation"
    model_dir.mkdir(exist_ok=True, parents=True)
    custom_py = pathlib.Path(model_dir, "custom.py")
    text = """
import pandas as pd
def load_model(code_dir):
    return True
def score(data, model, **kwargs):
    try:
        inp = {"question": data.iloc[0]["question"]}
        outputs = {"answer": f"You asked me \\"{inp['question']}\\""}
        rv = outputs["answer"]
    except Exception as e:
        rv = f"{e.__class__.__name__}: {str(e)}"
    return pd.DataFrame({"answer": [rv]})
    """
    custom_py.write_text(data=text)
    return model_dir


@pytest.fixture
def custom_model(dr_token: str, dr_endpoint: str, cleanup_dr) -> str:
    with cleanup_dr("customModels/"):
        custom_model = get_or_create_custom_model(
            endpoint=dr_endpoint,
            token=dr_token,
            name="pytest_cm",
            target_type="TextGeneration",
            target_name="answer",
        )
        yield custom_model


@pytest.fixture
def custom_model_version(
    dr_endpoint: str,
    dr_token: str,
    custom_model: str,
    custom_model_dir: pathlib.Path,
    cleanup_dr,
) -> str:
    with cleanup_dr(f"customModels/{custom_model}/versions"):
        custom_model_version = get_or_create_custom_model_version(
            dr_endpoint,
            dr_token,
            custom_model,
            base_environment_id="65f9b27eab986d30d4c64268",
            folder_path=custom_model_dir,
        )
        yield custom_model_version


@pytest.fixture
def cleanup_registered_models(cleanup_dr):
    with cleanup_dr("registeredModels/"):
        yield


@pytest.fixture
def registered_model_version(
    dr_endpoint: str,
    dr_token: str,
    custom_model_version: str,
    cleanup_registered_models,
) -> str:
    registered_model_version = get_or_create_registered_custom_model_version(
        dr_endpoint, dr_token, custom_model_version, "pytest_rmv"
    )
    yield registered_model_version


@pytest.fixture
def deployment(
    dr_endpoint: str,
    dr_token: str,
    registered_model_version: str,
    cleanup_dr,
) -> str:
    with cleanup_dr("deployments/"):
        deployment = get_or_create_deployment_from_registered_model_version(
            dr_endpoint,
            dr_token,
            registered_model_version,
            label="pytest_d",
            default_prediction_server_id="5f06612df1740600260aca72",
        )
        yield deployment


@pytest.fixture
def cleanup_validation(cleanup_dr):
    with cleanup_dr("genai/customModelLLMValidations/"):
        yield


@pytest.fixture
def prompt_column_name():
    return "question"


@pytest.fixture
def target_column_name():
    return "answer"


def test_get_or_create_custom_model_llm_validation(
    dr_token: str,
    dr_endpoint: str,
    deployment: str,
    prompt_column_name: str,
    target_column_name: str,
    cleanup_validation,
) -> None:
    validation_id = get_or_create_custom_model_llm_validation(
        endpoint=dr_endpoint,
        token=dr_token,
        prompt_column_name="question",
        target_column_name="answer",
        deployment_id=deployment,
    )
    assert len(validation_id)
    validation_id_2 = get_or_create_custom_model_llm_validation(
        endpoint=dr_endpoint,
        token=dr_token,
        prompt_column_name="question",
        target_column_name="answer",
        deployment_id=deployment,
    )
    assert validation_id == validation_id_2
