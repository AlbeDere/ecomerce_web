from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from hashlib import md5
# importing forms
from forms import RegisterForm, LoginForm, CreateItem, CommentForm
from config import SECRET_KEY, DATABASE_URI
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = 'static/assets/uploads/'
ckeditor = CKEditor(app)
Bootstrap5(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Adding profile images to the comment section
def gravatar_url(email, size=100, rating='g', default='retro', force_default=False):
    hash_value = md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_value}?s={size}&d={default}&r={rating}&f={force_default}"


# Creating database
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Configuring tables
class Items(db.Model):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Foreign Key, "users.id" the users refers to the tablename of User
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Reference to the User object. The "only_items" refers to the only_items property in the User class
    user = relationship("User", back_populates="only_items")
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    price: Mapped[str] = mapped_column(Integer, unique=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str] = mapped_column(String(250), nullable=True)
    # Parent relationship to the comments
    comments = relationship("Comment", back_populates="parent_item")

# Creating User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    # The "user" refers to the user property in the Items class
    only_items = relationship("Items", back_populates="user")
    # Parent relationship: "comment_author" refers to the comment_author property in the Comment class
    comments = relationship("Comment", back_populates="comment_author")


# Create a table for the comments on the products
class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Child relationship:"users.id" The users refers to the tablename of the User
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # The "comments" refers to the comments property in the User class
    comment_author = relationship("User", back_populates="comments")
    # Child Relationship to the Items
    product_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("items.id"))
    parent_item = relationship("Items", back_populates="comments")


with app.app_context():
    db.create_all()


# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the function
        return f(*args, **kwargs)
    return decorated_function

# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user email already exists
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # Inform user about existing registration
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        # Hash password
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        # Create new user record
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # Log in new user
        login_user(new_user)
        return redirect(url_for("home"))
    # Display registration form
    return render_template("register.html", form=form, current_user=current_user)

# Route for logging in
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Email in db is unique so will only have one result.
        user = result.scalar()
        # Case if email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Case if password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    # Display login form
    return render_template("login.html", form=form, current_user=current_user)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template("index.html")


# This route is for adding new items, accessible only by admin users
@app.route("/add_item", methods=["GET", "POST"])
@admin_only
def add_new_item():
    form = CreateItem()
    if form.validate_on_submit():
        # Secure and save the uploaded image
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(file_path)
        
        # Create and add new item to database
        new_item = Items(
            name=form.name.data,
            price=form.price.data,
            body=form.body.data,
            image_path = 'assets/uploads/' + filename,  
            user_id=current_user.id    # Associate item with current user
        )
        db.session.add(new_item)
        db.session.commit()
        # Redirect to the all products page after successful item addition
        return redirect(url_for("all_procucts"))
    # Render the add item form page
    return render_template("add_item.html", form=form, current_user=current_user)


# This route is for seeing individual products
@app.route("/item/<int:product_id>", methods=["GET", "POST"])
def show_product(product_id):
    # Fetch the item or show 404
    requested_item = db.get_or_404(Items, product_id)
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        # Ensure user is logged in before allowing to comment
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        
        # Create and save the new comment
        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_item=requested_item   # Associate comment with the item
        )
        db.session.add(new_comment)
        db.session.commit()

    # Render item details and comments form
    return render_template("show_product.html", item=requested_item, current_user=current_user, form=comment_form, gravatar_url=gravatar_url)


# This route is for editing product
@app.route("/edit-item/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    # Fetch item or show 404 error
    item = db.get_or_404(Items, product_id)
    # Pre-fill form with item's current details
    edit_form = CreateItem(
        name=item.name,
        price=item.price,
        body=item.body,
        image_path=item.image_path,
    )

    if edit_form.validate_on_submit():
        # Update item details with form data
        item.name = edit_form.name.data
        item.price = edit_form.price.data
        item.body = edit_form.body.data

        # Handle image update if a new image is uploaded
        if edit_form.image.data:
            filename = secure_filename(edit_form.image.data.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            edit_form.image.data.save(file_path)
            item.image_path = 'assets/uploads/' + filename  # Assuming 'uploads/' is the directory where images are saved

        db.session.commit()
        # Redirect to the updated item's page
        return redirect(url_for("show_product", product_id=item.id))
    # Render the edit item form page
    return render_template("add_item.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:product_id>")
@admin_only
def delete_product(product_id):
    # Fetch the item by id and delete it
    product_to_delete = db.get_or_404(Items, product_id)
    db.session.delete(product_to_delete)
    db.session.commit()
    # Redirect to the products listing page after deletion
    return redirect(url_for('all_procucts'))



@app.route("/all_procucts")
def all_procucts():
    result = db.session.execute(db.select(Items))
    items = result.scalars().all()
    return render_template("products.html", all_items=items, current_user=current_user)


# This route is for about page
@app.route("/about")
def about():
    return render_template("about.html")

# This route is for terms of service page
@app.route("/terms_of_service")
def terms_of_service():
    return render_template("tos.html")

# This route is for privacy policy page
@app.route("/privacy_policy")
def privacy_policy():
    return render_template("pp.html")



if __name__ == '__main__':
    app.run(debug=True)