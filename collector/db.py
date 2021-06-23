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
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(String)
    url = Column(String, nullable=False)
    folder_id = Column(Integer, ForeignKey('folder.id', name="folder_id"), nullable=False)

    folder = relationship('Folder', back_populates="bookmarks")


class Folder(Base):
    __tablename__ = 'folder'
    __table_args__ = (
        UniqueConstraint('name', 'parent_folder_id', name='_name_parent_uc'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    parent_folder_id = Column(Integer, ForeignKey('folder.id', name="parent_folder_id"), nullable=True)

    bookmarks = relationship('Bookmark', back_populates="folder")
    parent_folder = relationship('Folder', remote_side=[id], backref='children_folders')


@click.group()
def db():
    pass


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
    folders_id_tree = folders_tree_in_id()
    list_folders_tree_helper(folders_id_tree['0'], level=0)


def list_folders_tree_helper(folder_ids: [], level):
    if len(folder_ids) == 0:
        return
    for folder_id_tree in folder_ids:
        for k, v in folder_id_tree.items():
            with Session(engine) as session:
                # print(" " * 2 * level, )
                folder_name = session.execute(select(Folder).where(Folder.id == k)).first()[0].name
                print(" " * 5 * level, f'({level+1})', folder_name)
        list_folders_tree_helper(v, level=level + 1)


def folders_tree_in_id(parent_folder_id: int = None):
    """
    :param parent_folder_id:
    :return:
    """
    with Session(engine) as session:
        stmt = select(Folder).where(Folder.parent_folder_id == parent_folder_id)
        folders = session.execute(stmt).all()
        if len(folders) == 0:
            return {f'{parent_folder_id}': []}
        if parent_folder_id is None:
            parent_folder_id = 0
        return {f'{parent_folder_id}': [folders_tree_in_id(folder_tuple[0].id) for folder_tuple in folders]}


if __name__ == "__main__":
    # Base.metadata.drop_all(engine)
    # Base.metadata.create_all(engine)
    # create_default_folder()
    db()
