"""WTForms definitions for team and roster management."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from ..models import PlayerRole


class TeamForm(FlaskForm):
    name = StringField("Team name", validators=[DataRequired(), Length(max=80)])
    short_code = StringField("Short code", validators=[DataRequired(), Length(max=4)])
    submit = SubmitField("Save team")


class PlayerForm(FlaskForm):
    name = StringField("Player name", validators=[DataRequired(), Length(max=80)])
    role = SelectField(
        "Role",
        choices=[(role.value, role.value.replace("_", " ").title()) for role in PlayerRole],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save player")
