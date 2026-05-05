"""WTForms definitions for organiser match management."""

from __future__ import annotations

from wtforms import SelectField, SubmitField
from wtforms.fields.datetime import DateTimeLocalField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired


class MatchCreateForm(FlaskForm):
    team_a_id = SelectField("Team A", coerce=int, validators=[DataRequired()])
    team_b_id = SelectField("Team B", coerce=int, validators=[DataRequired()])
    scheduled_at = DateTimeLocalField(
        "Scheduled at", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    submit = SubmitField("Create match")
