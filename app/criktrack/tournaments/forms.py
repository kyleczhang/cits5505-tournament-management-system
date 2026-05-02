from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class TournamentCreateForm(FlaskForm):
    name = StringField(
        "Tournament name",
        validators=[DataRequired(), Length(max=120)],
    )
    description = TextAreaField(
        "Description", validators=[Optional(), Length(max=2000)]
    )
    format = SelectField(
        "Format",
        choices=[
            ("round_robin", "Round-robin"),
            ("knockout", "Knockout"),
            ("group_stage", "Group stage"),
        ],
        validators=[DataRequired()],
    )
    start_date = DateField("Start date", validators=[DataRequired()])
    num_teams = IntegerField(
        "Number of teams",
        validators=[DataRequired(), NumberRange(min=2, max=32)],
        default=6,
    )
    overs = IntegerField(
        "Overs per innings",
        validators=[Optional(), NumberRange(min=1, max=50)],
        default=20,
    )
    venue_name = StringField("Venue name", validators=[Optional(), Length(max=160)])
    venue_address = StringField(
        "Venue address", validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Create & continue")
