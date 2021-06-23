import time
from typing import Callable

import click

from sqlalchemy import create_engine
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String
from sqlalchemy.sql.expression import select
from sqlalchemy.future import Connection
from sqlalchemy.orm import declarative_base, relationship, Session

Base = declarative_base()
engine = create_engine("sqlite+pysqlite:///bookmarks.db", echo=False, future=True)


class Bookmark(Base):
    __tablename__ = 'bookmark'
    __table_args__ = (
        UniqueConstraint('title', 'folder_id', name='_title_folder_uc'),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    url = Column(String, nullable=False)
    folder_id = Column(Integer, ForeignKey('folder.id', name="folder_id"), nullable=False, default= 1)

    folder = relationship('Folder', back_populates="bookmarks")


class Folder(Base):
    __tablename__ = 'folder'
    __table_args__ = (
        UniqueConstraint('name', 'parent_folder_id', name='_name_description_parent_uc'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    parent_folder_id = Column(Integer, ForeignKey('folder.id', name="parent_folder_id"), nullable=False, default=0)

    bookmarks = relationship('Bookmark', back_populates="folder")
    parent_folder = relationship('Folder', remote_side=[id], backref='children_folders')


@click.group()
def db():
    pass


@db.command()
def init_db():
    Base.metadata.create_all(engine)
    create_default_folder()


@db.command()
def create_default_folder():
    with Session(engine) as session:
        folder = Folder()
        folder.name = "default"
        folder.description = "default folder"
        session.add(folder)
        session.commit()


@db.command()
@click.option('--name', help='name of folder')
@click.option('--description', default="", help='description of folder')
@click.option('--parent_folder_id', default=-1, help="id of parent folder")
def create_folder(name: str, description: str, parent_folder_id: int):
    with Session(engine) as session:
        folder = Folder()
        folder.name = name
        folder.description = description
        if parent_folder_id > 0:
            folder.parent_folder_id = parent_folder_id
        session.add(folder)
        session.commit()


@db.command()
def list_folders_tree():
    def print_folder_name(**kwargs):
        session = kwargs.pop('session')
        folder_id = kwargs.pop("folder_id")
        level = kwargs.pop("level")
        folder_name = session.execute(select(Folder).where(Folder.id == folder_id)).first()[0].name
        print(" " * 5 * level, f'({level + 1})', folder_name)

    folders_id_tree = folders_tree_in_id()
    list_helper(folders_id_tree['0'], 0, print_folder_name)


@db.command()
@click.option("--title")
@click.option("--description", default="")
@click.option("--url")
@click.option("--folder_id", default=1)
def create_bookmark(title: str, description: str, url: str, folder_id: int):
    with Session(engine) as session:
        bm = Bookmark()
        bm.title = title
        bm.description = description
        bm.url = url
        bm.folder_id = folder_id
        session.add(bm)
        session.commit()


@db.command()
def list_folders_bookmarks_tree():
    def f(**kwargs):
        session = kwargs.pop("session")
        folder_id = kwargs.pop("folder_id")
        level = kwargs.pop("level")
        folder_name = session.execute(select(Folder).where(Folder.id == folder_id)).first()[0].name
        print(" " * 5 * level, f'({level + 1})', folder_name)
        bookmarks = session.execute(select(Bookmark).where(Bookmark.folder_id == folder_id)).all()
        for bookmark_tuple in bookmarks:
            bookmark = bookmark_tuple[0]
            print(" ->" + " " * 5 * level,
                  f'title("{bookmark.title}"), description("{bookmark.description}"), url("{bookmark.url}")')

    folders_id_tree = folders_tree_in_id()
    list_helper(folders_id_tree['0'], 0, f)


def list_helper(folder_ids: [], level, f: Callable):
    if len(folder_ids) == 0:
        return
    for folder_id_tree in folder_ids:
        for k, v in folder_id_tree.items():
            with Session(engine) as session:
                f(session=session, folder_id=k, level=level)
            list_helper(v, level + 1, f)


def folders_tree_in_id(parent_folder_id: int = 0):
    """
    :param parent_folder_id:
    :return:
    """
    with Session(engine) as session:
        stmt = select(Folder).where(Folder.parent_folder_id == parent_folder_id)
        folders = session.execute(stmt).all()
        if len(folders) == 0:
            return {f'{parent_folder_id}': []}
        return {f'{parent_folder_id}': [folders_tree_in_id(folder_tuple[0].id) for folder_tuple in folders]}


if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    create_default_folder()
