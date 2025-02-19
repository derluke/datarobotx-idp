#
# Copyright 2024 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
#
# DataRobot, Inc.
#
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.
# https://www.datarobot.com/wp-content/uploads/2021/07/DataRobot-Tool-and-Utility-Agreement.pdf

import pandas as pd
import pytest

import datarobot as dr
from datarobot.models.model_registry.registered_model_version import ExternalTarget
from datarobotx.idp.autopilot import get_or_create_autopilot_run
from datarobotx.idp.custom_model_versions import get_or_create_custom_model_version
from datarobotx.idp.custom_models import get_or_create_custom_model
from datarobotx.idp.datasets import get_or_create_dataset_from_df
from datarobotx.idp.registered_model_versions import (
    _find_existing_registered_model,
    get_or_create_registered_custom_model_version,
    get_or_create_registered_external_model_version,
    get_or_create_registered_leaderboard_model_version,
)
from datarobotx.idp.use_cases import get_or_create_use_case


@pytest.fixture
def analyze_and_model_config():
    return {
        "target": "is_bad",
        "mode": "quick",
        "worker_count": -1,
    }


@pytest.fixture
def use_case(dr_endpoint, dr_token, cleanup_dr):
    with cleanup_dr("useCases/"):
        yield get_or_create_use_case(
            dr_endpoint,
            dr_token,
            "pytest use case #1",
        )


@pytest.fixture
def df():
    return (
        pd.read_csv(
            "https://s3.amazonaws.com/datarobot_public_datasets/10K_2007_to_2011_Lending_Club_Loans_v2_mod_80.csv"
        )
        .groupby("is_bad")
        .sample(n=50, random_state=42)
    )


@pytest.fixture
def dataset(dr_endpoint, dr_token, df, use_case, cleanup_dr):
    with cleanup_dr("datasets/", id_attribute="datasetId"):
        yield get_or_create_dataset_from_df(
            dr_endpoint,
            dr_token,
            use_case_id=use_case,
            name="pytest_test_autopilot_dataset",
            data_frame=df,
        )


@pytest.fixture
def autopilot_model(dr_endpoint, dr_token, use_case, dataset, analyze_and_model_config, cleanup_dr):
    with cleanup_dr("projects/", paginated=False):
        yield get_or_create_autopilot_run(
            dr_endpoint,
            dr_token,
            "pytest autopilot",
            dataset,
            analyze_and_model_config=analyze_and_model_config,
            use_case=use_case,
        )


@pytest.fixture()
def recommended_model(autopilot_model, cleanup_dr):
    return dr.ModelRecommendation.get(autopilot_model).model_id


@pytest.fixture
def custom_model(cleanup_dr, dr_endpoint, dr_token):
    with cleanup_dr("customModels/"):
        yield get_or_create_custom_model(
            dr_endpoint,
            dr_token,
            name="pytest custom model",
            target_type="Regression",
            target_name="foo",
        )


@pytest.fixture
def custom_model_version(
    cleanup_dr, custom_model, dr_endpoint, dr_token, folder_path, sklearn_drop_in_env
):
    with cleanup_dr(f"customModels/{custom_model}/versions/"):
        yield get_or_create_custom_model_version(
            dr_endpoint, dr_token, custom_model, sklearn_drop_in_env, folder_path
        )


@pytest.fixture
def cleanup_registered_models(cleanup_dr):
    with cleanup_dr("registeredModels/"):
        yield


@pytest.fixture
def external_model_target():
    return ExternalTarget(name="completion", type="Regression")


def test_get_or_create_from_custom_model(
    dr_endpoint, dr_token, cleanup_registered_models, custom_model_version
):
    model_1 = get_or_create_registered_custom_model_version(
        dr_endpoint, dr_token, custom_model_version, "pytest custom registered model #1"
    )
    assert len(model_1)

    model_2 = get_or_create_registered_custom_model_version(
        dr_endpoint, dr_token, custom_model_version, "pytest custom registered model #1"
    )
    assert model_1 == model_2

    model_3 = get_or_create_registered_custom_model_version(
        dr_endpoint, dr_token, custom_model_version, "pytest custom registered model #2"
    )
    assert model_1 != model_3

    model_4 = get_or_create_registered_custom_model_version(
        dr_endpoint,
        dr_token,
        custom_model_version,
        "pytest custom registered model #2",
        description="New description",
    )
    assert model_3 != model_4

    dr.Client(endpoint=dr_endpoint, token=dr_token)
    registered_model = _find_existing_registered_model("pytest custom registered model #2")
    versions = [version.id for version in registered_model.list_versions()]
    assert model_3 in versions and model_4 in versions


def test_get_or_create_external(
    dr_endpoint, dr_token, cleanup_registered_models, external_model_target
):
    model_1 = get_or_create_registered_external_model_version(
        dr_endpoint,
        dr_token,
        "pytest external registered model version #1",
        external_model_target,
        "pytest external registered model",
    )
    assert len(model_1)

    model_2 = get_or_create_registered_external_model_version(
        dr_endpoint,
        dr_token,
        "pytest external registered model version #1",
        external_model_target,
        "pytest external registered model",
    )
    assert model_1 == model_2

    model_3 = get_or_create_registered_external_model_version(
        dr_endpoint,
        dr_token,
        "pytest external registered model version #2",
        external_model_target,
        "pytest external registered model",
    )
    assert model_1 != model_3


def test_get_or_create_from_leaderboard(
    dr_endpoint, dr_token, cleanup_registered_models, recommended_model
):
    model_1 = get_or_create_registered_leaderboard_model_version(
        dr_endpoint,
        dr_token,
        recommended_model,
        "pytest datarobot registered model version #1",
    )
    assert len(model_1)

    model_2 = get_or_create_registered_leaderboard_model_version(
        dr_endpoint,
        dr_token,
        recommended_model,
        "pytest datarobot registered model version #1",
    )
    assert model_1 == model_2

    model_3 = get_or_create_registered_leaderboard_model_version(
        dr_endpoint,
        dr_token,
        recommended_model,
        "pytest datarobot registered model version #2",
    )
    assert model_1 != model_3
