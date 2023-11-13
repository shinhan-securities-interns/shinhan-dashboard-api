'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, TEXT, INT, BIGINT
import pandas as pd

DB_URL = 'mysql+pymysql://root:1234@localhost:3306/test'

class engineconn:
    def __init__(self):
        self.engine = create_engine(DB_URL, pool_recycle=500)
        Base.metadata.create_all(bind=self.engine)

    def sessionmaker(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session

    def connect(self):
        conn = self.engine.connect()
        return conn

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(BIGINT, nullable=False, autoincrement=True, primary_key=True)
    name = Column(TEXT, nullable=False)
    code = Column(TEXT, nullable=False)

engine = engineconn()
session = engine.sessionmaker()

if session.query(Stock).count() == 0:
    df = pd.read_csv('./단축코드_한글종목약명.csv')
    for index, row in df.iterrows():
        stock = Stock(name=row['한글 종목약명'], code=row['단축코드'])
        session.add(stock)

    session.commit()
    print("주식정보 추가")
else:
    print("주식정보가 있습니다.")
'''