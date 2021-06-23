import click

from db import db


@click.group()
def collector():
    pass


collector.add_command(db)

if __name__ == "__main__":
    collector()


