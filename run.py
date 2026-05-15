from app import create_app, db

app = create_app()

@app.cli.command("create-admin")
def create_admin():
    """Create an admin user."""
    from app.models.user import User
    import click
    
    email = click.prompt('Admin Email', type=str)
    username = click.prompt('Admin Username', type=str)
    password = click.prompt('Admin Password', hide_input=True, confirmation_prompt=True)
    
    if User.query.filter_by(email=email).first():
        click.echo('Error: User with this email already exists.')
        return
        
    user = User(email=email, username=username, first_name="System", last_name="Admin", is_admin=True, is_verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully!')

if __name__ == '__main__':
    app.run(debug=True)
