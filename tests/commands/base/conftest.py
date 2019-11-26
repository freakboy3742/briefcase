import pytest

from briefcase.commands.base import BaseCommand
from briefcase.config import AppConfig, GlobalConfig


class DummyCommand(BaseCommand):
    """
    A dummy command to test the BaseCommand interface.
    """
    platform = 'tester'
    output_format = 'dummy'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_options(self, parser):
        # Provide some extra arguments:
        # * some optional arguments
        parser.add_argument('-x', '--extra')
        parser.add_argument('-m', '--mystery')
        # * a required argument
        parser.add_argument('-r', '--required', required=True)

    def bundle_path(self, app):
        raise NotImplementedError()

    def binary_path(self, app):
        raise NotImplementedError()

    def distribution_path(self, app):
        raise NotImplementedError()


@pytest.fixture
def base_command(tmp_path):
    return DummyCommand(base_path=tmp_path)


# Define some stub command classes
# These will be used to test the command accessor
class DummyCreateCommand(DummyCommand):
    description = "Test Create"


class DummyUpdateCommand(DummyCommand):
    description = "Test Update"


class DummyBuildCommand(DummyCommand):
    description = "Test Build"


class DummyRunCommand(DummyCommand):
    description = "Test Run"


class DummyPublishCommand(DummyCommand):
    description = "Test Publish"


# Register the commands with the module
create = DummyCreateCommand
update = DummyUpdateCommand
build = DummyBuildCommand
run = DummyRunCommand
publish = DummyPublishCommand


# Define a command that defines a custom config class, and has no options.
class CustomGlobalConfig(GlobalConfig):
    def __init__(self, foo, **kwargs):
        super().__init__(**kwargs)
        self.foo = foo

    def __repr__(self):
        return '<Custom GlobalConfig {foo}>'.format(foo=self.foo)


class CustomAppConfig(AppConfig):
    def __init__(self, foo, bar, **kwargs):
        super().__init__(
            name='custom',
            bundle='com.example',
            description='Custom app',
            version="37.42"
        )
        self.foo = foo
        self.bar = bar

    def __repr__(self):
        return '<Custom AppConfig {foo}, {bar}>'.format(
            foo=self.foo,
            bar=self.bar
        )


class OtherDummyCommand(BaseCommand):
    GLOBAL_CONFIG_CLASS = CustomGlobalConfig
    APP_CONFIG_CLASS = CustomAppConfig

    platform = 'tester'
    output_format = 'dummy'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def bundle_path(self, app):
        raise NotImplementedError()

    def binary_path(self, app):
        raise NotImplementedError()

    def distribution_path(self, app):
        raise NotImplementedError()


@pytest.fixture
def other_command(tmp_path):
    return OtherDummyCommand(base_path=tmp_path)
