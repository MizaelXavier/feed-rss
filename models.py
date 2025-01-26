from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    # Converte a URL para o formato do SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')

# Configuração da engine com parâmetros recomendados pelo Neon
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # número máximo de conexões
    max_overflow=10,  # conexões adicionais que podem ser criadas além do pool_size
    pool_timeout=30,  # tempo máximo de espera por uma conexão
    pool_recycle=1800,  # recicla conexões após 30 minutos
    pool_pre_ping=True,  # verifica se a conexão está ativa antes de usar
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Fornece uma instância de sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enum para status do YouTube
class YoutubeStatus(enum.Enum):
    NOT_POSTED = "NOT_POSTED"
    POSTED = "POSTED"

# Modelo RSSFeed
class RSSFeed(Base):
    __tablename__ = 'rss_feed'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)  # Nome do monitor
    feed_url = Column(String, nullable=False)  # URL do feed RSS
    sheet_id = Column(String, nullable=False)  # ID da planilha Google Sheets
    is_active = Column(Boolean, default=True)  # Status do monitoramento
    last_check = Column(DateTime, nullable=True)  # Última verificação
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Modelo Creator
class Creator(Base):
    __tablename__ = 'creator'
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    videos = relationship("Video", back_populates="creator")

# Modelo Video
class Video(Base):
    __tablename__ = 'video'
    
    id = Column(String, primary_key=True)
    video_url = Column(String)
    youtube_url = Column(String, nullable=True)  # URL do vídeo no YouTube
    tiktok_id = Column(String, nullable=True)  # Nova coluna para o ID do TikTok
    local_path = Column(String, nullable=True)
    title = Column(String, nullable=True)  # Novo campo para o título do vídeo
    description = Column(Text, nullable=True)  # Nova coluna adicionada
    tags = Column(String, nullable=True)  # Nova coluna adicionada
    youtube_status = Column(Enum(YoutubeStatus), default=YoutubeStatus.NOT_POSTED)
    scheduled_time = Column(String(5), nullable=True)  # Novo campo para horário agendado
    youtube_date = Column(DateTime, nullable=True)  # Nova coluna para data de agendamento no YouTube
    created_at = Column(DateTime, default=datetime.utcnow)
    creator_id = Column(String, ForeignKey('creator.id'))
    creator = relationship("Creator", back_populates="videos")

# Criar tabelas
def init_db():
    """Inicializa o banco de dados criando as tabelas."""
    Base.metadata.create_all(bind=engine)

# Chamar init_db() ao importar o módulo
init_db() 