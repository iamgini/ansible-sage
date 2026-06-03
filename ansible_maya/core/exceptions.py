# Copyright 2026 Ansible AI Gateway Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom exceptions for Ansible Sage."""


class SageException(Exception):
    """Base exception for all Ansible Sage errors."""

    pass


class ConfigurationError(SageException):
    """Raised when configuration is invalid or missing."""

    pass


class LLMProviderError(SageException):
    """Base exception for LLM provider errors."""

    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when LLM provider rate limit is exceeded."""

    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when LLM provider authentication fails."""

    pass


class LLMUnavailableError(LLMProviderError):
    """Raised when LLM provider is unavailable."""

    pass


class PlaybookGenerationError(SageException):
    """Raised when playbook generation fails."""

    pass


class ValidationError(SageException):
    """Raised when validation fails (ansible-lint, YAML, etc.)."""

    pass


class AnsibleLintError(ValidationError):
    """Raised when ansible-lint validation fails."""

    def __init__(self, message: str, lint_output: str = None):
        super().__init__(message)
        self.lint_output = lint_output


class MoleculeTestError(ValidationError):
    """Raised when Molecule test execution fails."""

    def __init__(self, message: str, test_output: str = None):
        super().__init__(message)
        self.test_output = test_output


class YAMLValidationError(ValidationError):
    """Raised when YAML parsing or validation fails."""

    pass


class AAPIntegrationError(SageException):
    """Raised when AAP (Ansible Automation Platform) integration fails."""

    pass


class EventClassificationError(SageException):
    """Raised when event classification fails."""

    pass


class PlaybookExecutionError(SageException):
    """Raised when playbook execution fails."""

    pass
