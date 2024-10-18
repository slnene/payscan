from django.core.exceptions import ValidationError

class NumericPasswordValidator:
    def validate(self, password, user=None):
        if not password.isdigit() or len(password) != 5:
            raise ValidationError(
                "The password must contain exactly 5 numeric digits.",
                code='password_no_numeric',
            )

    def get_help_text(self):
        return "Your password must contain exactly 5 numeric digits."
