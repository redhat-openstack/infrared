import pytest

from infrared import api
from infrared.core.utils.exceptions import IRRequiredArgsMissingException, \
    IRExtraVarsException
from tests.test_execute import spec_fixture  # noqa
from tests.test_workspace import workspace_manager_fixture, test_workspace  # noqa


@pytest.mark.parametrize("cli_args, should_pass", [  # noqa
    ("--req-arg-a=yes", False),
    ("--req-arg-b=yes", False),
    ("--req-arg-a=yes --req-arg-b=yes", False),
    ("--req-arg-a=no --req-arg-b=yes", False),
    ("--req-arg-a=yes --req-arg-b=no", False),
    ("--req-arg-a=yes --uni-dep=uni-val", False),
    ("--req-arg-b=yes --multi-dep=multi-val", True),
    ("--req-arg-a=yes --uni-dep=uni-val --multi-dep=multi-val", True),
])
def test_required_when(spec_fixture, workspace_manager_fixture, test_workspace,
                       cli_args, should_pass):
    """Tests the 'required_when' mechanism

    :param spec_fixture: Fixtures which creates 'testing spec' (tests/example)
    :param workspace_manager_fixture: Fixture which sets the default workspace
      directory
    :param test_workspace: Fixture which creates temporary workspace directory
    :param cli_args: CLI arguments
    :param should_pass: Boolean value tells whether the test should pass or not
    :return:
    """
    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)

    if should_pass:
        rc = spec_manager.run_specs(args=['example'] + cli_args.split())
        assert rc == 0, "Execution failed, return code is: {}".format(rc)
    else:
        with pytest.raises(IRRequiredArgsMissingException):
            spec_manager.run_specs(args=['example'] + cli_args.split())


def test_extra_vars(spec_fixture, workspace_manager_fixture, test_workspace):
    """ Verify the --extra-vars parameter is validated"""
    spec_manager = api.SpecManager()
    spec_manager.register_spec(spec_fixture)

    workspace_manager_fixture.activate(test_workspace.name)
    assert spec_manager.run_specs(args=['example', '-e', 'key=value']) == 0

    with pytest.raises(IRExtraVarsException):
        spec_manager.run_specs(args=['example', '-e', 'key'])
