-- Polizas de ejemplo (ids 1..5)
INSERT INTO polizas (tipo, estado, canon_mensual, prima, porcentaje_ipc, fecha_inicio, fecha_fin) VALUES
('INDIVIDUAL', 'ACTIVA',    1500000.00, 180000.00, 5.20, '2025-01-01', '2026-01-01'),
('COLECTIVA',  'ACTIVA',    8000000.00, 950000.00, 5.20, '2025-03-01', '2026-03-01'),
('COLECTIVA',  'CANCELADA', 4200000.00, 500000.00, 4.80, '2024-06-01', '2025-06-01'),
('INDIVIDUAL', 'RENOVADA',  2100000.00, 250000.00, 5.20, '2025-07-15', '2026-07-15'),
('COLECTIVA',  'ACTIVA',    6500000.00, 780000.00, 5.20, '2025-09-01', '2026-09-01');

-- Riesgos de ejemplo (ids 1..8)
INSERT INTO riesgos (descripcion, direccion, valor_asegurado, estado, poliza_id) VALUES
('Apartamento 302',   'Calle 100 # 15-20, Bogotá',      1500000.00, 'ACTIVO',    1),
('Local comercial 1', 'Carrera 7 # 72-10, Bogotá',      3000000.00, 'ACTIVO',    2),
('Local comercial 2', 'Carrera 7 # 72-12, Bogotá',      2500000.00, 'ACTIVO',    2),
('Bodega norte',      'Autopista Norte # 180-50',       2500000.00, 'ACTIVO',    2),
('Oficina 501',       'Calle 26 # 68-35, Bogotá',       4200000.00, 'CANCELADO', 3),
('Casa campestre',    'Vereda La Calera, Cundinamarca', 2100000.00, 'ACTIVO',    4),
('Apartamento 1101',  'Calle 85 # 11-53, Bogotá',       3200000.00, 'ACTIVO',    5),
('Apartamento 1102',  'Calle 85 # 11-53, Bogotá',       3300000.00, 'ACTIVO',    5);
