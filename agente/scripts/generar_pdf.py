"""Genera el PDF de ejemplo con las condiciones generales del seguro.

Es un documento FICTICIO, escrito para la demostración. Sus reglas coinciden
con las de la API de pólizas (individual = un solo riesgo, renovación de un
año con IPC, cancelar la póliza cancela sus riesgos).

Uso, desde la carpeta agente/:
    python scripts/generar_pdf.py
"""

from pathlib import Path

from fpdf import FPDF

SALIDA = Path(__file__).resolve().parent.parent / "data" / "condiciones_generales.pdf"

TITULO = "CONDICIONES GENERALES - SEGURO DE ARRENDAMIENTO"
SUBTITULO = "Aseguradora Ejemplo S.A. - Documento ficticio creado para fines de demostración"

# Cada cláusula: (título, [párrafos]). El buscador fragmenta el PDF por estos títulos.
CLAUSULAS = [
    ("1. OBJETO DEL SEGURO", [
        "Este seguro ampara al arrendador contra el incumplimiento del arrendatario en el pago del "
        "canon mensual de arrendamiento y de los demás conceptos cubiertos, respecto de los inmuebles "
        "incluidos en la póliza como riesgos asegurados.",
    ]),
    ("2. DEFINICIONES", [
        "Tomador: persona que contrata el seguro y paga la prima. Asegurado: arrendador que recibe la "
        "indemnización. Arrendatario: persona que ocupa el inmueble y debe pagar el canon.",
        "Canon mensual: valor del arrendamiento pactado por mes. Prima: precio anual del seguro. "
        "Riesgo: cada inmueble asegurado, identificado por su descripción y dirección. Valor asegurado: "
        "monto máximo que la aseguradora paga por un riesgo. Siniestro: incumplimiento del arrendatario "
        "cubierto por esta póliza. IPC: índice de precios al consumidor pactado en la póliza.",
    ]),
    ("3. MODALIDADES DE PÓLIZA", [
        "Póliza individual: ampara un solo inmueble. No admite agregar más riesgos.",
        "Póliza colectiva: ampara varios inmuebles del mismo tomador. Mientras la póliza no esté "
        "cancelada se pueden agregar nuevos riesgos, y cada riesgo se puede cancelar por separado sin "
        "afectar a los demás.",
    ]),
    ("4. COBERTURAS BÁSICAS", [
        "a) Cánones de arrendamiento: hasta doce (12) cánones mensuales impagados por siniestro.",
        "b) Cuotas de administración: las cuotas impagadas que el contrato ponga a cargo del "
        "arrendatario, hasta doce (12) meses por siniestro.",
        "c) Servicios públicos: los saldos impagados de agua, energía y gas al momento de la "
        "restitución del inmueble, hasta dos (2) veces el canon mensual.",
    ]),
    ("5. COBERTURAS ADICIONALES", [
        "Se pueden contratar con prima adicional y deben figurar en la póliza:",
        "a) Daños al inmueble causados por el arrendatario, distintos del desgaste normal, hasta el "
        "diez por ciento (10%) del valor asegurado del riesgo.",
        "b) Gastos jurídicos del proceso de restitución del inmueble, hasta $5.000.000 por siniestro.",
    ]),
    ("6. EXCLUSIONES", [
        "La aseguradora no paga indemnización en los siguientes casos:",
        "a) Contratos de arrendamiento verbales o no firmados por las partes.",
        "b) Arrendatarios que ya estaban en mora antes del inicio de la vigencia de la póliza.",
        "c) Inmuebles destinados a actividades ilícitas.",
        "d) Daños por desgaste natural o por el uso normal del inmueble.",
        "e) Terremoto, inundación y otros eventos de la naturaleza; guerra, terrorismo o asonada.",
        "f) Intereses de mora, multas y cláusulas penales del contrato de arrendamiento.",
        "g) Cánones causados después de la restitución del inmueble.",
        "h) Contratos entre familiares hasta el segundo grado de consanguinidad.",
        "i) Aumentos del canon que no se informaron a la aseguradora.",
    ]),
    ("7. VIGENCIA", [
        "La póliza tiene una vigencia de un (1) año, contada desde la fecha de inicio hasta la fecha de "
        "fin indicadas en la póliza.",
    ]),
    ("8. RENOVACIÓN", [
        "La póliza se puede renovar por períodos sucesivos de un (1) año. Al renovarla, la nueva fecha "
        "de fin se extiende un año y el canon mensual y la prima se incrementan en el porcentaje de IPC "
        "pactado en la póliza. Por ejemplo, con un IPC de 5,2% un canon de $1.500.000 pasa a $1.578.000.",
        "No se puede renovar una póliza cancelada.",
    ]),
    ("9. CANCELACIÓN", [
        "El tomador puede cancelar la póliza en cualquier momento. La cancelación de la póliza cancela "
        "también todos sus riesgos. Una póliza cancelada no se puede reactivar ni renovar, y no se "
        "puede cancelar dos veces.",
        "Si el tomador cancela, la aseguradora devuelve la parte de la prima no devengada, en proporción "
        "al tiempo que faltaba de vigencia, dentro de los treinta (30) días hábiles siguientes. La "
        "aseguradora también puede revocar la póliza con aviso escrito de diez (10) días hábiles.",
    ]),
    ("10. PAGO DE LA PRIMA", [
        "La prima se paga dentro de los treinta (30) días calendario siguientes a la fecha de inicio o de "
        "renovación. La falta de pago en ese plazo termina automáticamente el contrato, conforme a la ley "
        "colombiana.",
    ]),
    ("11. AVISO DEL SINIESTRO", [
        "El asegurado debe avisar a la aseguradora dentro de los treinta (30) días calendario siguientes "
        "a la fecha de vencimiento del primer canon no pagado. Si avisa después, la aseguradora solo "
        "responde por los cánones vencidos a partir de la fecha del aviso.",
        "Documentos requeridos: copia del contrato de arrendamiento firmado, relación de cánones y "
        "cuotas adeudadas, documento de identidad del asegurado, certificado de tradición del inmueble "
        "y carta de reclamación.",
    ]),
    ("12. PAGO DE LA INDEMNIZACIÓN", [
        "La aseguradora paga dentro del mes siguiente a la entrega completa de los documentos del "
        "siniestro. De cada canon indemnizado se descuenta un deducible del diez por ciento (10%), que "
        "asume el asegurado. El total pagado por un riesgo nunca supera su valor asegurado.",
        "Una vez paga, la aseguradora queda subrogada en los derechos del asegurado para cobrarle al "
        "arrendatario lo pagado.",
    ]),
    ("13. PROTECCIÓN DE DATOS PERSONALES", [
        "Los datos personales del tomador, del asegurado y del arrendatario se tratan conforme a la "
        "Ley 1581 de 2012, únicamente para administrar la póliza y atender los siniestros.",
    ]),
    ("14. QUEJAS Y RECLAMOS", [
        "Las quejas se presentan por los canales de servicio al cliente de la aseguradora o ante el "
        "Defensor del Consumidor Financiero, que responde dentro de los quince (15) días hábiles "
        "siguientes.",
    ]),
]


class PDF(FPDF):
    def footer(self):
        # Pie de página en todas las hojas. {nb} se reemplaza por el total de páginas.
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()} de {{nb}} - Documento ficticio de ejemplo", align="C")


def main() -> None:
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, TITULO, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 6, SUBTITULO, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for titulo, parrafos in CLAUSULAS:
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 7, titulo, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for parrafo in parrafos:
            pdf.multi_cell(0, 5, parrafo, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)
        pdf.ln(2)

    SALIDA.parent.mkdir(exist_ok=True)
    pdf.output(str(SALIDA))
    print(f"PDF generado: {SALIDA} ({pdf.page_no()} páginas)")


if __name__ == "__main__":
    main()
