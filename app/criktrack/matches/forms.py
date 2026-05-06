"""WTForms definitions for organiser match management."""

from __future__ import annotations

from wtforms import SelectField, StringField, SubmitField
from wtforms.fields.datetime import DateTimeLocalField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Optional


class MatchCreateForm(FlaskForm):
    team_a_id = SelectField("Team A", coerce=int, validators=[DataRequired()])
    team_b_id = SelectField("Team B", coerce=int, validators=[DataRequired()])
    scheduled_at = DateTimeLocalField(
        "Scheduled at", format="%Y-%m-%dT%H:%M", validators=[DataRequired()]
    )
    venue_name = StringField(
        "Match venue name", validators=[Optional(), Length(max=160)]
    )
    venue_address = StringField(
        "Match venue address", validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Create match")
