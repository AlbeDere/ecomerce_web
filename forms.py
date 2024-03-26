from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileRequired
from flask_ckeditor import CKEditorField

# Form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Register", render_kw={'class': 'custom-button', 'style': 'text-align: right;'})

# Form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!", render_kw={'class': 'custom-button', 'style': 'text-align: right;'})

# Form to create products
class CreateItem(FlaskForm):
    name = StringField("Item name", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    body = CKEditorField("Description", validators=[DataRequired()])
    image = FileField("Item Picture", validators=[FileAllowed(['jpg','jpeg','png']), FileRequired()])
    submit = SubmitField("Create Item", render_kw={'class': 'custom-button', 'style': 'text-align: right;'})

# Form to add comments
class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment", render_kw={'class': 'custom-button', 'style': 'text-align: right;'})
    