-- Data Warehouse de Link Solutions (esquema en estrella) para Azure SQL / SQL Server.
-- Ejecutar sobre la base del almacén (por ejemplo db-dw), NO sobre la base de la tienda.

CREATE TABLE dim_fecha (
  fecha_key     INT PRIMARY KEY,            -- 20261029
  fecha         DATE NOT NULL,
  anio          SMALLINT,
  mes           TINYINT,
  nombre_mes    VARCHAR(15),
  trimestre     TINYINT,
  dia_semana    VARCHAR(12),
  es_fin_semana BIT
);

CREATE TABLE dim_producto (
  producto_key  INT IDENTITY PRIMARY KEY,
  sku           VARCHAR(100) NOT NULL UNIQUE,   -- llave natural, igual al SKU de nopCommerce
  nombre        NVARCHAR(400),
  categoria     NVARCHAR(200),
  precio_lista  DECIMAL(18,2)
);

CREATE TABLE dim_cliente (
  cliente_key       INT IDENTITY PRIMARY KEY,
  email             VARCHAR(320) NOT NULL UNIQUE, -- llave natural para unir tienda, CRM y comentarios
  nombre            NVARCHAR(200),
  tipo_cliente      VARCHAR(30),                  -- Individual / Empresa
  provincia         NVARCHAR(50),
  canal_adquisicion VARCHAR(50),
  fecha_registro    DATE
);

CREATE TABLE fact_ventas (
  venta_key       BIGINT IDENTITY PRIMARY KEY,
  pedido_id_nop   INT,
  linea_id_nop    INT,
  fecha_key       INT NOT NULL REFERENCES dim_fecha(fecha_key),
  producto_key    INT NOT NULL REFERENCES dim_producto(producto_key),
  cliente_key     INT NOT NULL REFERENCES dim_cliente(cliente_key),
  cantidad        INT,
  precio_unitario DECIMAL(18,2),
  total_linea     DECIMAL(18,2),
  origen          VARCHAR(20) NOT NULL DEFAULT 'tienda'   -- tienda / historico
);

CREATE TABLE fact_comentarios (
  comentario_key      BIGINT IDENTITY PRIMARY KEY,
  comentario_id       VARCHAR(50) NOT NULL UNIQUE,
  fecha_key           INT NOT NULL REFERENCES dim_fecha(fecha_key),
  producto_key        INT NOT NULL REFERENCES dim_producto(producto_key),
  cliente_key         INT NULL REFERENCES dim_cliente(cliente_key),
  red_social          VARCHAR(30),
  texto               NVARCHAR(MAX),
  sentimiento         VARCHAR(10) NULL,     -- positivo / neutro / negativo (lo llena el módulo de IA)
  puntaje_sentimiento FLOAT NULL
);

-- Tablas que llena el módulo de IA
CREATE TABLE pred_ventas (
  fecha            DATE NOT NULL,
  producto_key     INT NULL,                -- NULL = total de la tienda
  ventas_previstas DECIMAL(18,2),
  limite_inferior  DECIMAL(18,2),
  limite_superior  DECIMAL(18,2),
  generado_en      DATETIME2 DEFAULT SYSUTCDATETIME()
);

CREATE TABLE resumen_comentarios (
  producto_key INT NULL,
  periodo      VARCHAR(20),                 -- por ejemplo 2026-10
  resumen      NVARCHAR(MAX),
  generado_en  DATETIME2 DEFAULT SYSUTCDATETIME()
);

-- Predicción por producto generada por la red neuronal de demanda.
CREATE TABLE pred_demanda (
  fecha             DATE NOT NULL,
  producto_key      INT NOT NULL REFERENCES dim_producto(producto_key),
  demanda_prevista  DECIMAL(18,2) NOT NULL,
  generado_en       DATETIME2 DEFAULT SYSUTCDATETIME()
);

-- Índices para las consultas de Power BI
CREATE INDEX ix_fact_ventas_fecha    ON fact_ventas(fecha_key);
CREATE INDEX ix_fact_ventas_producto ON fact_ventas(producto_key);
CREATE INDEX ix_fact_ventas_cliente  ON fact_ventas(cliente_key);
CREATE INDEX ix_fact_coment_producto ON fact_comentarios(producto_key);
