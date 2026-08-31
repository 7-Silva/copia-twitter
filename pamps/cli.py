import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import Session, select, SQLModel
from faker import Faker

from .config import settings
from .db import engine
from .models import User,Post
from .models.user import UserRequest

main = typer.Typer(name="Pamps CLI")
fake = Faker("pt_BR")

@main.command()
def shell():
    """Opens interactive shell"""
    _vars = {
    "settings": settings,
    "engine": engine,
    "select": select,
    "session": Session(engine),
    "User": User,
    "Post":Post,
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython
        start_ipython(
        argv=["--ipython-dir=/tmp", "--no-banner"], user_ns=_vars
        )
    except ImportError:
        import code
        code.InteractiveConsole(_vars).interact()

@main.command()
def user_list():
    """Lists all users"""
    table = Table(title="Pamps users")
    fields = ["username", "email"]
    for header in fields:
        table.add_column(header, style="magenta")
    with Session(engine) as session:
        users = session.exec(select(User))
        for user in users:
            table.add_row(user.username, user.email)
    Console().print(table)


@main.command()
def create_user(email: str, username: str, password: str):
    """Create user teste 2"""
    with Session(engine) as session:
        request = UserRequest(email=email, username=username, password=password)
        user = User.model_validate(request)
        session.add(user)
        session.commit()
        session.refresh(user)
        typer.echo(f"created {username} user")
        return user

@main.command()
def create_user_random(
    quantidade: int = typer.Option(
        1, "--quantidade", "-q", help="Quantos usuários aleatórios criar"
    ),
):
    """Create one or more users with random data"""
    with Session(engine) as session:
        for _ in range(quantidade):
            username = fake.user_name()
            request = UserRequest(
                email=fake.unique.email(),
                username=username,
                password=fake.password(length=12),
                bio=fake.sentence(),
                avatar=fake.image_url(),
            )
            user = User.model_validate(request)
            session.add(user)
            session.commit()
            session.refresh(user)
            typer.echo(f"created {username} user")


@main.command()
def reset_db(force: bool = typer.Option(False, "--force", "-f", help="Run with no confirmation")):
    """Reset the database tables"""
    force = force or typer.confirm("Are you sure you want to reset the database?")
    if force:
        SQLModel.metadata.drop_all(engine)