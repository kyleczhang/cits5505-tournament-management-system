from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, Email, Length, Optional


class ProfileEditForm(FlaskForm):
    display_name = StringField(
        "Display name", validators=[DataRequired(), Length(max=80)]
    )
    email = StringField(
        "Email address", validators=[DataRequired(), Email(), Length(max=254)]
    )
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=240)])
    avatar_url = StringField(
        "Avatar URL", validators=[Optional(), URL(), Length(max=255)]
    )
    submit = SubmitField("Save changes")
