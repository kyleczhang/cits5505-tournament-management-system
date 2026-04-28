from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)

_PW_RULE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def _strong_password(_form, field):
    if not _PW_RULE.match(field.data or ""):
        raise ValidationError("Password must be ≥ 8 chars with letters and digits.")


class RegisterForm(FlaskForm):
    display_name = StringField("Full name", validators=[DataRequired(), Length(max=80)])
    email = StringField(
        "Email address", validators=[DataRequired(), Email(), Length(max=254)]
    )
    password = PasswordField("Password", validators=[DataRequired(), _strong_password])
    password_confirm = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    invite_code = StringField("Organizer invite code", validators=[Optional()])
    terms = BooleanField(
        "Accept terms",
        validators=[DataRequired(message="You must accept the terms.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class LogoutForm(FlaskForm):
    pass
