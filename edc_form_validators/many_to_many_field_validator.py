from django.forms import ValidationError
from edc_constants.constants import NOT_APPLICABLE

from .base_form_validator import BaseFormValidator
from .base_form_validator import NOT_APPLICABLE_ERROR, APPLICABLE_ERROR
from .base_form_validator import NOT_REQUIRED_ERROR, REQUIRED_ERROR, INVALID_ERROR


M2M_SELECTION_ONLY = 'm2m_selection_only'
M2M_INVALID_SELECTION = 'm2m_invalid_selection'


class ManyToManyFieldValidator(BaseFormValidator):

    def m2m_required(self, m2m_field=None):
        """Raises an exception or returns False.

        m2m_field is required.
        """
        message = None
        if not self.cleaned_data.get(m2m_field):
            message = {m2m_field: 'This field is required'}
            code = REQUIRED_ERROR
        if message:
            self._errors.update(message)
            self._error_codes.append(code)
            raise ValidationError(message, code=code)
        return False

    def m2m_required_if(self, response=None, field=None, m2m_field=None):
        """Raises an exception or returns False.

        m2m_field is required if field  == response
        """
        message = None
        if (self.cleaned_data.get(field) == response
                and not self.cleaned_data.get(m2m_field)):
            message = {m2m_field: 'This field is required'}
            code = REQUIRED_ERROR
        elif (self.cleaned_data.get(field) == response
              and self.cleaned_data.get(m2m_field).count() == 0):
            message = {m2m_field: 'This field is required'}
            code = REQUIRED_ERROR
        elif (self.cleaned_data.get(field) != response
              and self.cleaned_data.get(m2m_field)
              and self.cleaned_data.get(m2m_field).count() != 0):
            message = {m2m_field: 'This field is not required'}
            code = NOT_REQUIRED_ERROR
        if message:
            self._errors.update(message)
            self._error_codes.append(code)
            raise ValidationError(message, code=code)
        return False

    def m2m_single_selection_if(self, *single_selections, m2m_field=None):
        """Raises an exception of returns False.

        if a selected response from m2m_field is in single_selections
        and there is more than one selected value, raises.
        """
        qs = self.cleaned_data.get(m2m_field)
        if qs and qs.count() > 1:
            selected = {obj.short_name: obj.name for obj in qs}
            for selection in single_selections:
                if selection in selected:
                    message = {
                        m2m_field:
                        f'Invalid combination. \'{selected.get(selection)}\' '
                        f'may not be combined '
                        f'with other selections'}
                    self._errors.update(message)
                    self._error_codes.append(INVALID_ERROR)
                    raise ValidationError(message, code=INVALID_ERROR)
        return False

    def m2m_other_specify(self, *responses, m2m_field=None, field_other=None):
        """Raises an exception or returns False.

        field_other is required if a selected response from m2m_field
        is in responses

        Note: for edc list models, "short_name" is the stored value!
        """
        qs = self.cleaned_data.get(m2m_field)
        found = False
        if qs and qs.count() > 0:
            selected = {obj.short_name: obj.name for obj in qs}
            for response in responses:
                if response in selected:
                    found = True
            if found and not self.cleaned_data.get(field_other):
                message = {field_other: 'This field is required.'}
                self._errors.update(message)
                self._error_codes.append(REQUIRED_ERROR)
                raise ValidationError(message, code=REQUIRED_ERROR)
            elif not found and self.cleaned_data.get(field_other):
                message = {field_other: 'This field is not required.'}
                self._errors.update(message)
                self._error_codes.append(NOT_REQUIRED_ERROR)
                raise ValidationError(message, code=NOT_REQUIRED_ERROR)
        elif self.cleaned_data.get(field_other):
            message = {field_other: 'This field is not required.'}
            self._errors.update(message)
            self._error_codes.append(NOT_REQUIRED_ERROR)
            raise ValidationError(message, code=NOT_REQUIRED_ERROR)
        return False

    def m2m_other_specify_applicable(
            self, *responses, m2m_field=None, field_other=None):
        """Raises an exception or returns False.

        field_other is applicable if a selected response from m2m_field
        is in responses
        """
        qs = self.cleaned_data.get(m2m_field)
        found = False
        if qs and qs.count() > 0:
            selected = {obj.short_name: obj.name for obj in qs}
            for response in responses:
                if response in selected:
                    found = True
            if found and self.cleaned_data.get(field_other) == NOT_APPLICABLE:
                message = {field_other: 'This field is applicable.'}
                self._errors.update(message)
                self._error_codes.append(APPLICABLE_ERROR)
                raise ValidationError(message, code=APPLICABLE_ERROR)
            elif not found and self.cleaned_data.get(field_other) != NOT_APPLICABLE:
                message = {field_other: 'This field is not applicable.'}
                self._errors.update(message)
                self._error_codes.append(NOT_APPLICABLE_ERROR)
                raise ValidationError(message, code=NOT_APPLICABLE_ERROR)
        elif self.cleaned_data.get(field_other) != NOT_APPLICABLE:
            message = {field_other: 'This field is not applicable.'}
            self._errors.update(message)
            self._error_codes.append(NOT_APPLICABLE_ERROR)
            raise ValidationError(message, code=NOT_APPLICABLE_ERROR)
        return False

    def m2m_selection_expected(self, response, m2m_field=None, error_msg=None):
        """Raises an exception or returns False.

        m2m_field is required and the selection must be `response`
        and only `response`.
        """
        qs = self.cleaned_data.get(m2m_field)
        if qs and qs.count() > 0:
            selection = [
                obj.short_name for obj in qs if obj.short_name == response]
            if not selection or qs.count() > 1:
                message = {
                    m2m_field: error_msg or f'Expected {response} only.'}
                self._errors.update(message)
                self._error_codes.append(M2M_SELECTION_ONLY)
                raise ValidationError(message, code=M2M_SELECTION_ONLY)
        return False

    def m2m_selections_not_expected(self, *responses, m2m_field=None, error_msg=None):
        """Raises an exception or returns False.

        m2m_field is required but no selections may be in `responses`.
        """
        qs = self.cleaned_data.get(m2m_field)
        if qs and qs.count() > 0:
            selections = [
                obj.short_name for obj in qs if obj.short_name in responses]
            if selections:
                display_names = ', '.join([
                    obj.name for obj in qs if obj.short_name in responses])
                message = {
                    m2m_field: error_msg or (f'Invalid selection. '
                                             f'Cannot be any of: {display_names}.')}
                self._errors.update(message)
                self._error_codes.append(M2M_INVALID_SELECTION)
                raise ValidationError(message, code=M2M_INVALID_SELECTION)
        return False
