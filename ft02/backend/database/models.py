from sqlalchemy import Column, String, Integer, Float, Boolean
from backend.database.db import Base


class Business(Base):
    __tablename__ = "businesses"

    gstin = Column(String, primary_key=True)
    business_name = Column(String)
    state = Column(String)
    industry = Column(String)
    registration_year = Column(Integer)
    business_age = Column(Integer)


class GSTFiling(Base):
    __tablename__ = "gst_filings"

    filing_id = Column(Integer, primary_key=True)
    gstin = Column(String)
    month = Column(String)
    filing_delay_days = Column(Integer)
    invoice_count = Column(Integer)
    sales_value = Column(Float)


class UPITransaction(Base):
    __tablename__ = "upi_transactions"

    transaction_id = Column(Integer, primary_key=True)
    sender_gstin = Column(String)
    receiver_gstin = Column(String)
    amount = Column(Float)


class EWayShipment(Base):
    __tablename__ = "eway_shipments"

    shipment_id = Column(Integer, primary_key=True)
    gstin = Column(String)
    origin = Column(String)
    destination = Column(String)
    shipment_value = Column(Float)