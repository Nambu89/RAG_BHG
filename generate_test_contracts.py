"""
Generador de contratos de prueba para BHG RAG MVP
Crea contratos PDF detallados para testing
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from datetime import datetime, timedelta
import os
from pathlib import Path

class ContractGenerator:
    def __init__(self, output_dir="data/contracts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Crea estilos personalizados para el contrato"""
        # Estilo para título
        self.styles.add(ParagraphStyle(
            name='ContractTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=30,
            alignment=TA_CENTER,
            bold=True
        ))
        
        # Estilo para cláusulas
        self.styles.add(ParagraphStyle(
            name='ClauseTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12,
            spaceBefore=20,
            bold=True
        ))
        
        # Estilo para texto justificado
        self.styles.add(ParagraphStyle(
            name='Justified',
            parent=self.styles['BodyText'],
            alignment=TA_JUSTIFY,
            fontSize=11,
            leading=16,
            spaceAfter=12
        ))
        
    def generate_hotel_management_contract(self):
        """Genera contrato de gestión hotelera"""
        filename = "contrato_gestion_hotelera_BHG.pdf"
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE GESTIÓN HOTELERA", self.styles['ContractTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Partes
        parties_text = """En Palma de Mallorca, a 15 de enero de 2024.<br/><br/>
        
        <b>REUNIDOS</b><br/><br/>
        
        De una parte, <b>BARCELÓ HOTEL GROUP, S.A.</b>, con CIF A-07015275, domiciliada en 
        Calle José Rover Motta, 27, 07006 Palma de Mallorca, inscrita en el Registro Mercantil 
        de Palma de Mallorca, Tomo 1234, Folio 56, Hoja PM-78901, representada en este acto por 
        D. Miguel Ángel Barceló Sánchez, mayor de edad, con DNI 12345678A, en su calidad de 
        Director General de Operaciones, con poderes suficientes para este acto según escritura 
        pública otorgada ante el Notario de Palma de Mallorca, D. Juan García López, el día 
        10 de marzo de 2022, con número de protocolo 456 (en adelante, el <b>"GESTOR"</b>).<br/><br/>
        
        Y de otra parte, <b>MEDITERRANEAN RESORT INVESTMENTS, S.L.</b>, con CIF B-98765432, 
        domiciliada en Avenida del Puerto, 123, 46023 Valencia, inscrita en el Registro 
        Mercantil de Valencia, Tomo 5678, Folio 90, Hoja V-123456, representada en este acto 
        por Dña. Carmen Martínez Ruiz, mayor de edad, con DNI 87654321B, en su calidad de 
        Administradora Única, con poderes suficientes según escritura pública otorgada ante 
        el Notario de Valencia, D. Pedro Fernández Silva, el día 5 de julio de 2023, con 
        número de protocolo 789 (en adelante, la <b>"PROPIEDAD"</b>).<br/><br/>
        
        Ambas partes, reconociéndose mutuamente capacidad legal suficiente para contratar y 
        obligarse, libre y espontáneamente,<br/><br/>
        
        <b>EXPONEN</b><br/><br/>
        
        <b>I.</b> Que la PROPIEDAD es titular del pleno dominio del establecimiento hotelero 
        denominado <b>"HOTEL MEDITERRÁNEO BEACH RESORT"</b>, de categoría 5 estrellas, con 
        350 habitaciones, situado en Playa de la Malvarrosa, Paseo Marítimo 456, 46011 Valencia, 
        inscrito en el Registro de Empresas y Actividades Turísticas de la Comunidad Valenciana 
        con el número H-VA-2024-001.<br/><br/>
        
        <b>II.</b> Que el GESTOR es una empresa líder en el sector hotelero, con amplia 
        experiencia en la gestión de establecimientos turísticos de alta categoría, contando 
        con más de 270 hoteles en 24 países y reconocido prestigio internacional.<br/><br/>
        
        <b>III.</b> Que la PROPIEDAD está interesada en que el GESTOR se encargue de la 
        gestión integral del Hotel, aportando su know-how, sistemas de gestión, marca y 
        canales de comercialización.<br/><br/>
        
        <b>IV.</b> Que ambas partes han llegado a un acuerdo para la gestión del Hotel, 
        que se regirá por las siguientes,<br/><br/>
        
        <b>CLÁUSULAS</b>"""
        
        story.append(Paragraph(parties_text, self.styles['Justified']))
        story.append(PageBreak())
        
        # Cláusulas principales
        clauses = [
            {
                "title": "PRIMERA.- OBJETO DEL CONTRATO",
                "content": """El presente contrato tiene por objeto regular las condiciones bajo las cuales el GESTOR 
                asumirá la gestión integral del HOTEL MEDITERRÁNEO BEACH RESORT, incluyendo pero no limitándose a:
                <br/><br/>
                a) La dirección y administración general del Hotel<br/>
                b) La gestión comercial y de marketing<br/>
                c) La gestión de reservas a través de los sistemas y canales del GESTOR<br/>
                d) La gestión del personal<br/>
                e) La gestión de compras y proveedores<br/>
                f) La gestión financiera y contable<br/>
                g) La implementación de los estándares de calidad Barceló<br/>
                h) La gestión del mantenimiento y conservación<br/><br/>
                
                El GESTOR operará el Hotel bajo la marca "Barceló" o cualquier otra marca del grupo que 
                las partes acuerden, comprometiéndose a mantener los estándares de calidad asociados a 
                dicha marca."""
            },
            {
                "title": "SEGUNDA.- DURACIÓN",
                "content": """El presente contrato tendrá una duración inicial de <b>QUINCE (15) AÑOS</b>, contados 
                a partir del 1 de abril de 2024, fecha prevista para el inicio de la gestión, una vez 
                finalizadas las obras de renovación previstas en la Cláusula Decimoquinta.<br/><br/>
                
                El contrato se prorrogará automáticamente por períodos sucesivos de <b>CINCO (5) AÑOS</b>, 
                salvo que cualquiera de las partes comunique a la otra su voluntad de no prorrogarlo con 
                una antelación mínima de <b>DOCE (12) MESES</b> a la fecha de vencimiento del período 
                inicial o de cualquiera de sus prórrogas.<br/><br/>
                
                No obstante lo anterior, el GESTOR tendrá derecho a dar por terminado el contrato de 
                forma anticipada en caso de que el GOP (Gross Operating Profit) acumulado durante dos 
                ejercicios consecutivos sea negativo, con un preaviso de seis (6) meses."""
            },
            {
                "title": "TERCERA.- CANON DE GESTIÓN",
                "content": """Como contraprestación por los servicios de gestión, la PROPIEDAD abonará al GESTOR 
                los siguientes conceptos:<br/><br/>
                
                <b>3.1. Canon Base (Base Fee):</b><br/>
                Un <b>TRES POR CIENTO (3%)</b> sobre los Ingresos Totales del Hotel. Se entiende por 
                Ingresos Totales la suma de todos los ingresos operativos del Hotel, incluyendo 
                habitaciones, alimentación y bebidas, spa, eventos y otros ingresos operativos, 
                excluyendo el IVA.<br/><br/>
                
                <b>3.2. Canon de Incentivo (Incentive Fee):</b><br/>
                Un <b>OCHO POR CIENTO (8%)</b> sobre el GOP (Gross Operating Profit) del Hotel. 
                El GOP se calculará según los Uniform System of Accounts for the Lodging Industry 
                (USALI) en su edición más reciente.<br/><br/>
                
                <b>3.3. Canon Mínimo Garantizado:</b><br/>
                El GESTOR percibirá un canon mínimo garantizado de <b>SEISCIENTOS MIL EUROS (600.000€)</b> 
                anuales, que se ajustará anualmente según el IPC. En caso de que la suma del Canon Base 
                y el Canon de Incentivo no alcance esta cantidad, la PROPIEDAD abonará la diferencia.<br/><br/>
                
                <b>3.4. Fees de Comercialización y Marketing:</b><br/>
                Adicionalmente, la PROPIEDAD contribuirá con un <b>DOS POR CIENTO (2%)</b> de los 
                Ingresos Totales por Habitaciones al fondo de marketing del grupo Barceló.<br/><br/>
                
                <b>3.5. Fees por Servicios Centralizados:</b><br/>
                Un <b>UNO POR CIENTO (1%)</b> de los Ingresos Totales en concepto de servicios 
                centralizados (sistemas de reservas, tecnología, formación, etc.)."""
            },
            {
                "title": "CUARTA.- OBLIGACIONES DEL GESTOR",
                "content": """El GESTOR se compromete a:<br/><br/>
                
                a) Gestionar el Hotel con la diligencia de un ordenado empresario y conforme a los 
                estándares de calidad de Barceló Hotel Group<br/><br/>
                
                b) Elaborar y ejecutar el Plan de Negocio Anual, que deberá ser aprobado por la PROPIEDAD<br/><br/>
                
                c) Mantener los seguros necesarios para la operación del Hotel<br/><br/>
                
                d) Proporcionar informes mensuales de gestión, incluyendo P&L, ocupación, ADR, RevPAR 
                y otros KPIs relevantes<br/><br/>
                
                e) Implementar y mantener los sistemas de calidad y sostenibilidad del grupo<br/><br/>
                
                f) Gestionar el personal conforme a la legislación laboral vigente<br/><br/>
                
                g) Mantener la contabilidad del Hotel de forma separada<br/><br/>
                
                h) Comercializar el Hotel a través de todos los canales del grupo<br/><br/>
                
                i) Implementar los programas de fidelización del grupo<br/><br/>
                
                j) Realizar auditorías de calidad trimestrales"""
            },
            {
                "title": "QUINTA.- OBLIGACIONES DE LA PROPIEDAD",
                "content": """La PROPIEDAD se compromete a:<br/><br/>
                
                a) Mantener la propiedad del Hotel libre de cargas y gravámenes que impidan su normal 
                explotación<br/><br/>
                
                b) Realizar las inversiones de capital (CapEx) necesarias, con un mínimo anual del 
                <b>CUATRO POR CIENTO (4%)</b> de los Ingresos Totales<br/><br/>
                
                c) Constituir un Fondo de Reserva para Reposición (FF&E Reserve) equivalente al 
                <b>TRES POR CIENTO (3%)</b> de los Ingresos Totales anuales<br/><br/>
                
                d) Aprobar el Plan de Negocio Anual en un plazo máximo de 30 días desde su presentación<br/><br/>
                
                e) Facilitar al GESTOR los fondos necesarios para la operación del Hotel<br/><br/>
                
                f) Mantener vigentes las licencias y permisos necesarios<br/><br/>
                
                g) No interferir en la gestión diaria del Hotel<br/><br/>
                
                h) Abonar puntualmente los cánones de gestión"""
            },
            {
                "title": "SEXTA.- PERSONAL",
                "content": """<b>6.1. Subrogación:</b><br/>
                El GESTOR se subrogará en los contratos de trabajo del personal actual del Hotel, 
                conforme a lo establecido en el convenio colectivo aplicable.<br/><br/>
                
                <b>6.2. Dirección del Hotel:</b><br/>
                El Director General del Hotel será nombrado por el GESTOR, previa consulta con la 
                PROPIEDAD. Los puestos directivos clave (Director de Operaciones, Director Comercial, 
                Director Financiero) serán designados por el GESTOR.<br/><br/>
                
                <b>6.3. Políticas de Personal:</b><br/>
                El personal se regirá por las políticas y procedimientos del grupo Barceló, incluyendo 
                formación, evaluación del desempeño y desarrollo profesional.<br/><br/>
                
                <b>6.4. Costes de Personal:</b><br/>
                Todos los costes de personal, incluyendo salarios, seguros sociales, indemnizaciones 
                y otros beneficios, serán por cuenta del Hotel y se reflejarán en su P&L."""
            },
            {
                "title": "SÉPTIMA.- CUENTAS BANCARIAS Y GESTIÓN FINANCIERA",
                "content": """<b>7.1. Cuentas Operativas:</b><br/>
                Se abrirán cuentas bancarias a nombre de la PROPIEDAD para la operación del Hotel, 
                sobre las cuales el GESTOR tendrá poderes de disposición para la gestión ordinaria.<br/><br/>
                
                <b>7.2. Límites de Disposición:</b><br/>
                El GESTOR podrá disponer libremente para gastos operativos hasta <b>CINCUENTA MIL 
                EUROS (50.000€)</b> por operación. Para importes superiores, se requerirá autorización 
                previa de la PROPIEDAD.<br/><br/>
                
                <b>7.3. Cash Management:</b><br/>
                El GESTOR implementará un sistema de cash management eficiente, manteniendo un fondo 
                de maniobra equivalente a 45 días de gastos operativos.<br/><br/>
                
                <b>7.4. Distribución de Beneficios:</b><br/>
                Mensualmente, después de cubrir todos los gastos operativos, cánones de gestión y 
                reservas obligatorias, el excedente se transferirá a la cuenta designada por la PROPIEDAD."""
            },
            {
                "title": "OCTAVA.- SEGUROS",
                "content": """<b>8.1. Seguros Obligatorios:</b><br/>
                La PROPIEDAD mantendrá vigentes los siguientes seguros:<br/>
                - Seguro de daños materiales (continente): valor de reconstrucción<br/>
                - Seguro de responsabilidad civil: mínimo 6.000.000€<br/>
                - Seguro de pérdida de beneficios: 12 meses de GOP estimado<br/><br/>
                
                <b>8.2. Seguros del GESTOR:</b><br/>
                El GESTOR mantendrá un seguro de responsabilidad civil profesional con cobertura 
                mínima de 3.000.000€ por siniestro.<br/><br/>
                
                <b>8.3. Gestión de Siniestros:</b><br/>
                El GESTOR gestionará las reclamaciones de seguros en nombre de la PROPIEDAD, 
                informando de cualquier siniestro en un plazo máximo de 48 horas."""
            },
            {
                "title": "NOVENA.- MARKETING Y COMERCIALIZACIÓN",
                "content": """<b>9.1. Estrategia de Marketing:</b><br/>
                El GESTOR desarrollará e implementará la estrategia de marketing del Hotel, incluyendo:<br/>
                - Plan de marketing anual<br/>
                - Gestión de la reputación online<br/>
                - Campañas publicitarias<br/>
                - Participación en ferias y eventos<br/>
                - Gestión de redes sociales<br/><br/>
                
                <b>9.2. Canales de Distribución:</b><br/>
                El Hotel se comercializará a través de:<br/>
                - Sistema central de reservas Barceló<br/>
                - Página web del grupo y del hotel<br/>
                - GDS (Global Distribution Systems)<br/>
                - OTAs (Online Travel Agencies)<br/>
                - Canal MICE (Meetings, Incentives, Conferences, Exhibitions)<br/><br/>
                
                <b>9.3. Revenue Management:</b><br/>
                El GESTOR aplicará técnicas avanzadas de revenue management para optimizar los ingresos, 
                con revisión diaria de tarifas y disponibilidad.<br/><br/>
                
                <b>9.4. Programa de Fidelización:</b><br/>
                El Hotel participará en el programa my Barceló, reconociendo los beneficios 
                correspondientes a los miembros."""
            },
            {
                "title": "DÉCIMA.- ESTÁNDARES DE CALIDAD",
                "content": """<b>10.1. Estándares Barceló:</b><br/>
                El Hotel operará conforme a los estándares de calidad establecidos por Barceló Hotel 
                Group para hoteles de 5 estrellas, incluyendo:<br/>
                - Estándares de servicio<br/>
                - Estándares de limpieza y mantenimiento<br/>
                - Estándares de F&B<br/>
                - Estándares de sostenibilidad<br/><br/>
                
                <b>10.2. Auditorías de Calidad:</b><br/>
                Se realizarán auditorías trimestrales, con un objetivo mínimo de cumplimiento del 85%. 
                El incumplimiento reiterado podrá dar lugar a la resolución del contrato.<br/><br/>
                
                <b>10.3. Mystery Guest:</b><br/>
                Se realizarán evaluaciones mystery guest al menos dos veces al año.<br/><br/>
                
                <b>10.4. Certificaciones:</b><br/>
                El GESTOR mantendrá las certificaciones de calidad y sostenibilidad requeridas 
                (ISO 9001, ISO 14001, etc.)."""
            },
            {
                "title": "UNDÉCIMA.- TECNOLOGÍA Y SISTEMAS",
                "content": """<b>11.1. Sistemas Operativos:</b><br/>
                El GESTOR implementará los siguientes sistemas:<br/>
                - PMS (Property Management System): Opera Cloud o similar<br/>
                - POS (Point of Sale) para F&B<br/>
                - Sistema de revenue management<br/>
                - CRM (Customer Relationship Management)<br/>
                - Sistema de gestión de mantenimiento<br/><br/>
                
                <b>11.2. Conectividad:</b><br/>
                La PROPIEDAD garantizará conectividad de alta velocidad (mínimo 1 Gbps simétrico) 
                y WiFi de calidad en todo el Hotel.<br/><br/>
                
                <b>11.3. Ciberseguridad:</b><br/>
                El GESTOR implementará protocolos de ciberseguridad conforme a la normativa vigente, 
                incluyendo RGPD.<br/><br/>
                
                <b>11.4. Actualizaciones:</b><br/>
                Los costes de licencias y actualizaciones de software serán gastos operativos del Hotel."""
            },
            {
                "title": "DUODÉCIMA.- REPORTING Y CONTROL",
                "content": """<b>12.1. Informes Mensuales:</b><br/>
                El GESTOR proporcionará antes del día 15 de cada mes:<br/>
                - P&L detallado del mes anterior<br/>
                - Informe de ocupación, ADR y RevPAR<br/>
                - Análisis de segmentación de mercado<br/>
                - Informe de cash flow<br/>
                - KPIs operativos<br/><br/>
                
                <b>12.2. Presupuesto Anual:</b><br/>
                Antes del 1 de noviembre de cada año, el GESTOR presentará el presupuesto para el 
                año siguiente, incluyendo:<br/>
                - P&L proyectado<br/>
                - Plan de marketing<br/>
                - Plan de inversiones (CapEx)<br/>
                - Plan de personal<br/><br/>
                
                <b>12.3. Comité de Gestión:</b><br/>
                Se constituirá un Comité de Gestión que se reunirá trimestralmente, formado por 
                2 representantes de cada parte.<br/><br/>
                
                <b>12.4. Acceso a Información:</b><br/>
                La PROPIEDAD tendrá acceso en tiempo real a los sistemas de información del Hotel."""
            },
            {
                "title": "DECIMOTERCERA.- TERMINACIÓN ANTICIPADA",
                "content": """<b>13.1. Causas de Resolución por la PROPIEDAD:</b><br/>
                a) Incumplimiento grave de los estándares de calidad (puntuación inferior a 75% en 
                dos auditorías consecutivas)<br/>
                b) GOP negativo durante tres ejercicios consecutivos<br/>
                c) Incumplimiento de obligaciones esenciales del GESTOR<br/>
                d) Pérdida de la marca Barceló por causas imputables al GESTOR<br/><br/>
                
                <b>13.2. Causas de Resolución por el GESTOR:</b><br/>
                a) Impago de los cánones de gestión durante más de 90 días<br/>
                b) Incumplimiento del plan de inversiones acordado<br/>
                c) Interferencia reiterada en la gestión<br/>
                d) Cambio de control de la PROPIEDAD sin consentimiento<br/><br/>
                
                <b>13.3. Procedimiento:</b><br/>
                La parte afectada notificará el incumplimiento, otorgando 60 días para subsanarlo. 
                De no subsanarse, podrá resolver el contrato con efectos a los 6 meses.<br/><br/>
                
                <b>13.4. Indemnización:</b><br/>
                En caso de resolución anticipada sin causa justificada:<br/>
                - Por la PROPIEDAD: 3 años de canon mínimo garantizado<br/>
                - Por el GESTOR: 1 año de canon mínimo garantizado"""
            },
            {
                "title": "DECIMOCUARTA.- COMPETENCIA Y CONFIDENCIALIDAD",
                "content": """<b>14.1. No Competencia:</b><br/>
                Durante la vigencia del contrato y por 2 años después, la PROPIEDAD no podrá:<br/>
                - Gestionar directamente el Hotel<br/>
                - Contratar a otro operador para el Hotel<br/>
                - Desarrollar hoteles competidores en un radio de 5 km<br/><br/>
                
                <b>14.2. Confidencialidad:</b><br/>
                Ambas partes mantendrán confidencial toda la información comercial, financiera y 
                operativa, durante la vigencia del contrato y por 5 años después.<br/><br/>
                
                <b>14.3. Propiedad Intelectual:</b><br/>
                El know-how, procedimientos y sistemas del GESTOR seguirán siendo de su propiedad. 
                La PROPIEDAD no podrá utilizarlos tras la terminación del contrato.<br/><br/>
                
                <b>14.4. Datos de Clientes:</b><br/>
                La base de datos de clientes será copropiedad, pudiendo ambas partes utilizarla 
                conforme al RGPD."""
            },
            {
                "title": "DECIMOQUINTA.- INVERSIÓN INICIAL Y RENOVACIÓN",
                "content": """<b>15.1. Plan de Renovación:</b><br/>
                La PROPIEDAD se compromete a realizar una inversión inicial de <b>DIEZ MILLONES 
                DE EUROS (10.000.000€)</b> en la renovación integral del Hotel, conforme al proyecto 
                aprobado por ambas partes.<br/><br/>
                
                <b>15.2. Calendario:</b><br/>
                - Inicio obras: 1 de febrero de 2024<br/>
                - Finalización prevista: 31 de marzo de 2024<br/>
                - Apertura soft: 1 de abril de 2024<br/>
                - Gran apertura: 1 de mayo de 2024<br/><br/>
                
                <b>15.3. Supervisión:</b><br/>
                El GESTOR supervisará las obras para garantizar el cumplimiento de los estándares 
                Barceló. Cualquier modificación al proyecto deberá ser aprobada por el GESTOR.<br/><br/>
                
                <b>15.4. Penalizaciones:</b><br/>
                Por cada día de retraso en la entrega, la PROPIEDAD compensará al GESTOR con 5.000€/día, 
                hasta un máximo de 500.000€."""
            },
            {
                "title": "DECIMOSEXTA.- MISCELÁNEA",
                "content": """<b>16.1. Legislación Aplicable:</b><br/>
                Este contrato se regirá por la legislación española.<br/><br/>
                
                <b>16.2. Jurisdicción:</b><br/>
                Las partes se someten a los Juzgados y Tribunales de Palma de Mallorca, con renuncia 
                a cualquier otro fuero.<br/><br/>
                
                <b>16.3. Arbitraje:</b><br/>
                Para controversias superiores a 100.000€, las partes podrán someterse a arbitraje 
                de la Corte de Arbitraje de la Cámara de Comercio de Madrid.<br/><br/>
                
                <b>16.4. Notificaciones:</b><br/>
                Las notificaciones se realizarán por burofax o correo certificado a las direcciones 
                indicadas en el encabezamiento.<br/><br/>
                
                <b>16.5. Integridad:</b><br/>
                Este contrato constituye la totalidad del acuerdo entre las partes, dejando sin 
                efecto cualquier acuerdo anterior.<br/><br/>
                
                <b>16.6. Modificaciones:</b><br/>
                Cualquier modificación deberá constar por escrito y ser firmada por ambas partes."""
            }
        ]
        
        # Añadir cada cláusula
        for clause in clauses:
            story.append(Paragraph(clause["title"], self.styles['ClauseTitle']))
            story.append(Paragraph(clause["content"], self.styles['Justified']))
            
        # Firmas
        story.append(PageBreak())
        story.append(Paragraph("FIRMAS", self.styles['ClauseTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Tabla de firmas
        firma_data = [
            ["POR EL GESTOR", "POR LA PROPIEDAD"],
            ["", ""],
            ["", ""],
            ["_" * 40, "_" * 40],
            ["D. Miguel Ángel Barceló Sánchez", "Dña. Carmen Martínez Ruiz"],
            ["BARCELÓ HOTEL GROUP, S.A.", "MEDITERRANEAN RESORT INVESTMENTS, S.L."]
        ]
        
        firma_table = Table(firma_data, colWidths=[3.5*inch, 3.5*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 2), (-1, 2), 40),
        ]))
        
        story.append(firma_table)
        
        # Generar PDF
        doc.build(story)
        print(f"✅ Generado: {filename}")
        
    def generate_service_contract(self):
        """Genera contrato de servicios"""
        filename = "contrato_servicios_mantenimiento_BHG.pdf"
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE PRESTACIÓN DE SERVICIOS DE MANTENIMIENTO", self.styles['ContractTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Contenido del contrato
        intro_text = """En Madrid, a 20 de febrero de 2024.<br/><br/>
        
        <b>REUNIDOS</b><br/><br/>
        
        De una parte, <b>BARCELÓ HOTEL GROUP, S.A.</b>, con CIF A-07015275 y domicilio en 
        Calle José Rover Motta, 27, 07006 Palma de Mallorca, representada por D. Carlos 
        Fernández García, Director de Compras y Servicios Generales (en adelante, el <b>"CLIENTE"</b>).<br/><br/>
        
        De otra parte, <b>TECHNICAL MAINTENANCE SOLUTIONS, S.L.</b>, con CIF B-28123456 y 
        domicilio en Calle Industria, 45, 28020 Madrid, representada por D. Roberto Sánchez 
        López, en calidad de Administrador Único (en adelante, el <b>"PROVEEDOR"</b>).<br/><br/>
        
        <b>EXPONEN</b><br/><br/>
        
        Que el CLIENTE precisa contratar servicios especializados de mantenimiento integral 
        para sus establecimientos hoteleros en la zona centro de España, y el PROVEEDOR cuenta 
        con la experiencia y medios necesarios para prestar dichos servicios.<br/><br/>
        
        <b>CLÁUSULAS</b>"""
        
        story.append(Paragraph(intro_text, self.styles['Justified']))
        
        # Cláusulas del contrato de servicios
        service_clauses = [
            {
                "title": "PRIMERA.- OBJETO",
                "content": """El PROVEEDOR prestará al CLIENTE servicios de mantenimiento integral que incluyen:
                <br/><br/>
                <b>1.1. Mantenimiento Preventivo:</b><br/>
                - Revisión mensual de instalaciones eléctricas<br/>
                - Revisión trimestral de sistemas de climatización<br/>
                - Revisión semestral de grupos de presión y bombeo<br/>
                - Revisión anual de calderas y ACS<br/>
                - Mantenimiento de piscinas y spa<br/>
                - Revisión de ascensores (subcontratado a empresa autorizada)<br/><br/>
                
                <b>1.2. Mantenimiento Correctivo:</b><br/>
                - Servicio 24/7 para emergencias<br/>
                - Tiempo de respuesta: 2 horas para emergencias, 24 horas para incidencias normales<br/>
                - Mano de obra incluida para reparaciones<br/>
                - Materiales y repuestos por cuenta del CLIENTE<br/><br/>
                
                <b>1.3. Gestión Técnica:</b><br/>
                - Software GMAO (Gestión de Mantenimiento Asistido por Ordenador)<br/>
                - Informes mensuales de actividad<br/>
                - Plan anual de mantenimiento<br/>
                - Gestión de subcontratas especializadas"""
            },
            {
                "title": "SEGUNDA.- ÁMBITO DE APLICACIÓN",
                "content": """Los servicios se prestarán en los siguientes establecimientos del CLIENTE:
                <br/><br/>
                - Barceló Torre de Madrid (5*) - 258 habitaciones<br/>
                - Barceló Emperatriz (5*) - 146 habitaciones<br/>
                - Barceló Imagine (5*) - 156 habitaciones<br/>
                - Occidental Castellana Norte (4*) - 144 habitaciones<br/>
                - Occidental Pera (4*) - 133 habitaciones<br/><br/>
                
                Total: 5 hoteles, 837 habitaciones<br/><br/>
                
                La incorporación de nuevos establecimientos requerirá adenda al contrato con 
                revisión de precios."""
            },
            {
                "title": "TERCERA.- PRECIO Y FORMA DE PAGO",
                "content": """<b>3.1. Precio:</b><br/>
                El precio total por los servicios será de <b>CUARENTA Y CINCO MIL EUROS (45.000€)</b> 
                mensuales más IVA, lo que supone 540.000€ anuales más IVA.<br/><br/>
                
                <b>3.2. Revisión de Precios:</b><br/>
                El precio se revisará anualmente según el IPC publicado por el INE, con un máximo 
                del 3% anual.<br/><br/>
                
                <b>3.3. Facturación:</b><br/>
                Facturación mensual, a mes vencido. Las facturas se emitirán el día 1 de cada mes 
                por los servicios del mes anterior.<br/><br/>
                
                <b>3.4. Forma de Pago:</b><br/>
                Transferencia bancaria a 60 días fecha factura. En caso de retraso, se aplicará 
                el interés legal del dinero más 2 puntos.<br/><br/>
                
                <b>3.5. Servicios Adicionales:</b><br/>
                Los servicios fuera del alcance definido se presupuestarán aparte y se facturarán 
                según las tarifas acordadas en el Anexo I."""
            },
            {
                "title": "CUARTA.- DURACIÓN",
                "content": """El contrato tendrá una duración de <b>TRES (3) AÑOS</b> desde el 1 de marzo 
                de 2024, prorrogable tácitamente por períodos anuales salvo denuncia con 3 meses 
                de antelación.<br/><br/>
                
                Durante el primer año, ninguna de las partes podrá resolver el contrato salvo 
                incumplimiento grave."""
            },
            {
                "title": "QUINTA.- PERSONAL",
                "content": """<b>5.1. Equipo Mínimo:</b><br/>
                El PROVEEDOR asignará como mínimo:<br/>
                - 1 Jefe de Mantenimiento (dedicación 100%)<br/>
                - 3 Oficiales de mantenimiento (dedicación 100%)<br/>
                - 2 Ayudantes (dedicación 100%)<br/>
                - 1 Técnico de guardia (noches y fines de semana)<br/><br/>
                
                <b>5.2. Cualificación:</b><br/>
                Todo el personal deberá contar con:<br/>
                - Formación profesional en electricidad/fontanería<br/>
                - Carné de instalador autorizado según especialidad<br/>
                - Formación en PRL<br/>
                - Experiencia mínima 2 años en hoteles<br/><br/>
                
                <b>5.3. Sustituciones:</b><br/>
                El PROVEEDOR garantizará la cobertura de bajas, vacaciones y ausencias sin 
                coste adicional."""
            },
            {
                "title": "SEXTA.- OBLIGACIONES DEL PROVEEDOR",
                "content": """El PROVEEDOR se obliga a:<br/><br/>
                
                a) Cumplir el Plan de Mantenimiento Preventivo acordado<br/>
                b) Atender las emergencias en los tiempos establecidos<br/>
                c) Mantener un stock mínimo de repuestos críticos<br/>
                d) Proporcionar uniformes e identificación a su personal<br/>
                e) Mantener vigente seguro de RC por importe mínimo de 3.000.000€<br/>
                f) Cumplir toda la normativa aplicable, especialmente en PRL<br/>
                g) Mantener la confidencialidad sobre la información del CLIENTE<br/>
                h) Implantar y mantener el sistema GMAO<br/>
                i) Formar a su personal en los estándares Barceló<br/>
                j) Participar en las reuniones mensuales de seguimiento"""
            },
            {
                "title": "SÉPTIMA.- OBLIGACIONES DEL CLIENTE",
                "content": """El CLIENTE se obliga a:<br/><br/>
                
                a) Facilitar el acceso a todas las instalaciones<br/>
                b) Proporcionar un espacio para almacén y vestuarios<br/>
                c) Abonar puntualmente las facturas<br/>
                d) Aprobar los presupuestos de materiales en 48 horas<br/>
                e) Designar un interlocutor único por hotel<br/>
                f) Facilitar los planos e históricos de las instalaciones<br/>
                g) Comunicar las incidencias a través del sistema acordado<br/>
                h) No contratar directamente al personal del PROVEEDOR durante la vigencia 
                del contrato y 1 año después"""
            },
            {
                "title": "OCTAVA.- NIVEL DE SERVICIO (SLA)",
                "content": """<b>8.1. Indicadores:</b><br/>
                - Disponibilidad del servicio: 99%<br/>
                - Tiempo respuesta emergencias: máximo 2 horas<br/>
                - Tiempo resolución emergencias: máximo 8 horas<br/>
                - Cumplimiento plan preventivo: mínimo 95%<br/>
                - Satisfacción cliente: mínimo 8/10<br/><br/>
                
                <b>8.2. Penalizaciones:</b><br/>
                - Por cada hora de retraso en emergencias: 500€<br/>
                - Por incumplimiento plan preventivo: 2% dto. factura mensual por cada 5% de incumplimiento<br/>
                - Por disponibilidad inferior al 99%: 1.000€ por cada punto porcentual<br/><br/>
                
                <b>8.3. Medición:</b><br/>
                Los KPIs se medirán mensualmente a través del sistema GMAO y se revisarán en 
                las reuniones de seguimiento."""
            },
            {
                "title": "NOVENA.- SEGUROS Y RESPONSABILIDADES",
                "content": """<b>9.1. Seguros del PROVEEDOR:</b><br/>
                - RC General: 3.000.000€<br/>
                - RC Patronal: 600.000€ por víctima<br/>
                - Accidentes convenio colectivo<br/><br/>
                
                <b>9.2. Responsabilidades:</b><br/>
                El PROVEEDOR responderá de:<br/>
                - Daños causados por negligencia de su personal<br/>
                - Pérdidas por falta de mantenimiento adecuado<br/>
                - Sanciones por incumplimiento normativo en su ámbito<br/><br/>
                
                <b>9.3. Limitación:</b><br/>
                La responsabilidad máxima del PROVEEDOR será el importe anual del contrato, 
                salvo dolo o negligencia grave."""
            },
            {
                "title": "DÉCIMA.- RESOLUCIÓN",
                "content": """<b>10.1. Causas de Resolución:</b><br/>
                - Incumplimiento grave de obligaciones<br/>
                - Incumplimiento reiterado de SLAs (3 meses consecutivos)<br/>
                - Insolvencia o concurso de cualquiera de las partes<br/>
                - Falta de pago de 3 mensualidades<br/>
                - Pérdida de autorizaciones necesarias<br/><br/>
                
                <b>10.2. Procedimiento:</b><br/>
                Preaviso de 30 días para subsanar, salvo imposibilidad material.<br/><br/>
                
                <b>10.3. Efectos:</b><br/>
                En caso de resolución, el PROVEEDOR entregará toda la documentación técnica 
                y facilitará la transición durante 1 mes."""
            }
        ]
        
        # Añadir cláusulas
        for clause in service_clauses:
            story.append(Paragraph(clause["title"], self.styles['ClauseTitle']))
            story.append(Paragraph(clause["content"], self.styles['Justified']))
            
        # Añadir anexo
        story.append(PageBreak())
        story.append(Paragraph("ANEXO I - TARIFAS SERVICIOS ADICIONALES", self.styles['ClauseTitle']))
        
        # Tabla de tarifas
        tarifa_data = [
            ["Concepto", "Precio/Hora", "Precio/Hora Festivo"],
            ["Oficial 1ª", "35€", "50€"],
            ["Oficial 2ª", "30€", "45€"],
            ["Ayudante", "25€", "38€"],
            ["Desplazamiento urgente", "50€", "75€"],
            ["Hora ingeniería", "65€", "N/A"]
        ]
        
        tarifa_table = Table(tarifa_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        tarifa_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tarifa_table)
        
        # Firmas
        story.append(PageBreak())
        story.append(Paragraph("En prueba de conformidad, firman las partes por duplicado:", 
                              self.styles['Justified']))
        story.append(Spacer(1, 1*inch))
        
        # Tabla de firmas
        firma_data = [
            ["POR EL CLIENTE", "POR EL PROVEEDOR"],
            ["", ""],
            ["_" * 40, "_" * 40],
            ["D. Carlos Fernández García", "D. Roberto Sánchez López"],
            ["BARCELÓ HOTEL GROUP, S.A.", "TECHNICAL MAINTENANCE SOLUTIONS, S.L."]
        ]
        
        firma_table = Table(firma_data, colWidths=[3.5*inch, 3.5*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 1), (-1, 1), 40),
        ]))
        
        story.append(firma_table)
        
        # Generar PDF
        doc.build(story)
        print(f"✅ Generado: {filename}")

    def generate_franchise_contract(self):
        """Genera contrato de franquicia"""
        filename = "contrato_franquicia_hoteles_BHG.pdf"
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE FRANQUICIA HOTELERA", self.styles['ContractTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Contenido
        intro = """En Barcelona, a 25 de marzo de 2024.<br/><br/>
        
        <b>REUNIDOS</b><br/><br/>
        
        De una parte, <b>BARCELÓ HOTEL GROUP, S.A.</b> (el <b>"FRANQUICIADOR"</b>), con CIF A-07015275,
        representada por Dña. Ana María Barceló Tous, Directora de Desarrollo y Franquicias.<br/><br/>
        
        De otra parte, <b>COSTA BRAVA RESORTS, S.L.</b> (el <b>"FRANQUICIADO"</b>), con CIF B-17654321,
        representada por D. Josep Puig i Cadafalch, Administrador Único.<br/><br/>
        
        <b>EXPONEN</b><br/><br/>
        
        I. Que el FRANQUICIADOR es titular de la marca "Occidental Hotels & Resorts" y ha desarrollado
        un sistema de gestión hotelera de reconocido prestigio internacional.<br/><br/>
        
        II. Que el FRANQUICIADO es propietario del Hotel Costa Brava Palace, de 4 estrellas y 180
        habitaciones, situado en Lloret de Mar, y desea integrarse en la red Occidental.<br/><br/>
        
        III. Que ambas partes han acordado formalizar un contrato de franquicia hotelera bajo las
        siguientes <b>CLÁUSULAS</b>:"""
        
        story.append(Paragraph(intro, self.styles['Justified']))
        
        # Cláusulas principales de franquicia
        franchise_clauses = [
            {
                "title": "PRIMERA.- OBJETO Y ALCANCE DE LA FRANQUICIA",
                "content": """<b>1.1.</b> El FRANQUICIADOR concede al FRANQUICIADO el derecho no exclusivo a:
                <br/><br/>
                a) Operar el Hotel bajo la marca "Occidental Costa Brava"<br/>
                b) Utilizar el know-how y sistemas de gestión del FRANQUICIADOR<br/>
                c) Acceder al sistema central de reservas<br/>
                d) Beneficiarse de las campañas de marketing corporativo<br/>
                e) Utilizar los manuales operativos y de estándares<br/><br/>
                
                <b>1.2.</b> El FRANQUICIADO operará el Hotel de forma independiente, asumiendo todos
                los riesgos empresariales y responsabilidades.<br/><br/>
                
                <b>1.3.</b> La franquicia se limita al Hotel identificado, no pudiendo extenderse a
                otros establecimientos sin nuevo acuerdo."""
            },
            {
                "title": "SEGUNDA.- DURACIÓN Y TERRITORIO",
                "content": """<b>2.1. Duración:</b> DIEZ (10) AÑOS desde el 1 de junio de 2024, renovable
                por períodos de 5 años.<br/><br/>
                
                <b>2.2. Territorio:</b> El Hotel ubicado en Avenida del Mar, 123, Lloret de Mar, Girona.<br/><br/>
                
                <b>2.3. Exclusividad Territorial:</b> El FRANQUICIADOR no otorgará otra franquicia
                Occidental en un radio de 3 km durante los primeros 5 años."""
            },
            {
                "title": "TERCERA.- CANON DE FRANQUICIA Y FEES",
                "content": """El FRANQUICIADO abonará:<br/><br/>
                
                <b>3.1. Canon Inicial (Initial Fee):</b> CIENTO CINCUENTA MIL EUROS (150.000€), 
                pagaderos a la firma.<br/><br/>
                
                <b>3.2. Royalty:</b> CINCO POR CIENTO (5%) de los Ingresos Brutos por Habitación 
                mensuales.<br/><br/>
                
                <b>3.3. Fee de Marketing:</b> DOS POR CIENTO (2%) de los Ingresos Brutos por 
                Habitación para el fondo común de marketing.<br/><br/>
                
                <b>3.4. Fee de Reservas:</b> 15€ por cada reserva confirmada a través del sistema 
                central.<br/><br/>
                
                <b>3.5. Otros Fees:</b><br/>
                - Programa fidelización: 3€ por estancia de miembro<br/>
                - Formación adicional: según tarifas vigentes<br/>
                - Auditorías extra: 1.500€ por auditoría"""
            },
            {
                "title": "CUARTA.- INVERSIONES Y ESTÁNDARES",
                "content": """<b>4.1. Inversión Inicial:</b> El FRANQUICIADO invertirá mínimo 3.000.000€ 
                en adaptar el Hotel a los estándares Occidental antes de la apertura.<br/><br/>
                
                <b>4.2. PIP (Property Improvement Plan):</b> Cumplir el plan de mejoras acordado en 
                el Anexo II.<br/><br/>
                
                <b>4.3. Mantenimiento:</b> Destinar mínimo 3% de ingresos anuales a mantenimiento y 
                renovación.<br/><br/>
                
                <b>4.4. Renovaciones Periódicas:</b><br/>
                - Soft goods (textiles): cada 3 años<br/>
                - Case goods (mobiliario): cada 7 años<br/>
                - Renovación completa: cada 12 años"""
            },
            {
                "title": "QUINTA.- OBLIGACIONES DEL FRANQUICIADOR",
                "content": """El FRANQUICIADOR se compromete a:<br/><br/>
                
                a) Proporcionar el Manual de Operaciones y Estándares<br/>
                b) Formar al personal directivo (40 horas iniciales)<br/>
                c) Asistencia en la pre-apertura (2 semanas in situ)<br/>
                d) Incluir el Hotel en todos los canales de distribución<br/>
                e) Proporcionar acceso a las plataformas tecnológicas<br/>
                f) Realizar 2 visitas anuales de soporte<br/>
                g) Actualizar continuamente los sistemas y procedimientos<br/>
                h) Defender y proteger la marca<br/>
                i) Gestionar el programa de fidelización<br/>
                j) Desarrollar campañas de marketing nacional e internacional"""
            },
            {
                "title": "SEXTA.- OBLIGACIONES DEL FRANQUICIADO",
                "content": """El FRANQUICIADO se obliga a:<br/><br/>
                
                a) Operar el Hotel 365 días al año, 24 horas<br/>
                b) Mantener los estándares de calidad Occidental (mínimo 85% en auditorías)<br/>
                c) Implementar todos los sistemas y procedimientos<br/>
                d) Participar en todas las promociones corporativas<br/>
                e) Mantener las certificaciones requeridas<br/>
                f) Contratar los seguros mínimos establecidos<br/>
                g) Reportar diariamente las estadísticas operativas<br/>
                h) Permitir auditorías e inspecciones<br/>
                i) No realizar modificaciones sin autorización<br/>
                j) Mantener confidencialidad absoluta del know-how"""
            },
            {
                "title": "SÉPTIMA.- MARKETING Y COMERCIALIZACIÓN",
                "content": """<b>7.1. Marca:</b> Uso obligatorio de "Occidental Costa Brava" en toda 
                comunicación.<br/><br/>
                
                <b>7.2. Estándares Gráficos:</b> Cumplir el manual de identidad corporativa.<br/><br/>
                
                <b>7.3. Marketing Local:</b> Destinar mínimo 1% de ingresos adicional al fee común.<br/><br/>
                
                <b>7.4. Aprobaciones:</b> Toda publicidad local requiere aprobación previa.<br/><br/>
                
                <b>7.5. Online:</b> La web del hotel será una subpágina de occidentalhotels.com<br/><br/>
                
                <b>7.6. Redes Sociales:</b> Gestionadas según protocolo corporativo."""
            },
            {
                "title": "OCTAVA.- FORMACIÓN Y ASISTENCIA TÉCNICA",
                "content": """<b>8.1. Formación Inicial:</b><br/>
                - Director General: 2 semanas en hotel modelo<br/>
                - Jefes Departamento: 1 semana formación específica<br/>
                - Personal base: formación in situ pre-apertura<br/><br/>
                
                <b>8.2. Formación Continua:</b><br/>
                - Webinars mensuales obligatorios<br/>
                - Convention anual (asistencia obligatoria dirección)<br/>
                - Actualizaciones online<br/><br/>
                
                <b>8.3. Costes:</b> Formación inicial incluida. Adicional según tarifas.<br/><br/>
                
                <b>8.4. Idiomas:</b> Formación disponible en español e inglés."""
            },
            {
                "title": "NOVENA.- TECNOLOGÍA Y SISTEMAS",
                "content": """<b>9.1. Sistemas Obligatorios:</b><br/>
                - PMS: Opera Cloud o compatible<br/>
                - CRS: Sistema Barceló<br/>
                - Revenue Management: Ideas o similar<br/>
                - CRM corporativo<br/><br/>
                
                <b>9.2. Costes:</b> Licencias y mantenimiento por cuenta del FRANQUICIADO.<br/><br/>
                
                <b>9.3. Datos:</b> Compartir todos los datos operativos en tiempo real.<br/><br/>
                
                <b>9.4. PCI Compliance:</b> Mantener certificación PCI-DSS vigente."""
            },
            {
                "title": "DÉCIMA.- CALIDAD Y AUDITORÍAS",
                "content": """<b>10.1. Auditorías:</b><br/>
                - Trimestrales el primer año<br/>
                - Semestrales a partir del segundo año<br/>
                - Mystery guest anual<br/><br/>
                
                <b>10.2. Estándares Mínimos:</b><br/>
                - Puntuación auditoría: 85%<br/>
                - Satisfacción clientes: 8.5/10<br/>
                - RevPAR Index: 100 mínimo<br/>
                - Online reputation: 4.0/5.0<br/><br/>
                
                <b>10.3. Planes de Mejora:</b> Obligatorios si no se alcanzan estándares, con 
                plazos específicos.<br/><br/>
                
                <b>10.4. Consecuencias:</b> Tres auditorías consecutivas por debajo del 80% son 
                causa de resolución."""
            },
            {
                "title": "UNDÉCIMA.- TERMINACIÓN Y EFECTOS",
                "content": """<b>11.1. Causas de Terminación:</b><br/>
                a) Vencimiento del plazo sin renovación<br/>
                b) Incumplimiento grave de estándares<br/>
                c) Impago de fees durante 60 días<br/>
                d) Daño a la marca<br/>
                e) Cambio de control no autorizado<br/>
                f) Insolvencia o concurso<br/><br/>
                
                <b>11.2. Efectos de la Terminación:</b><br/>
                - Cese inmediato uso de marca<br/>
                - Desvinculación de sistemas<br/>
                - Eliminación de signos distintivos (plazo 30 días)<br/>
                - Devolución de manuales y materiales<br/>
                - Pago de fees pendientes<br/><br/>
                
                <b>11.3. No Competencia:</b> 2 años en radio de 10 km."""
            },
            {
                "title": "DUODÉCIMA.- TRANSMISIÓN Y CAMBIO DE CONTROL",
                "content": """<b>12.1. Derecho de Tanteo:</b> El FRANQUICIADOR tendrá derecho preferente 
                de compra del Hotel.<br/><br/>
                
                <b>12.2. Autorización:</b> Cualquier transmisión requiere autorización previa y 
                escrita.<br/><br/>
                
                <b>12.3. Condiciones:</b> El nuevo franquiciado deberá cumplir los criterios de 
                selección y firmar nuevo contrato.<br/><br/>
                
                <b>12.4. Fee de Transmisión:</b> 50.000€ por cambio de titularidad autorizado."""
            },
            {
                "title": "DECIMOTERCERA.- SEGUROS Y RESPONSABILIDADES",
                "content": """<b>13.1. Seguros Mínimos:</b><br/>
                - RC General: 6.000.000€<br/>
                - Daños materiales: valor reconstrucción<br/>
                - Pérdida beneficios: 12 meses<br/>
                - RC productos: 3.000.000€<br/><br/>
                
                <b>13.2. Beneficiario Adicional:</b> El FRANQUICIADOR constará como beneficiario 
                adicional en pólizas de RC.<br/><br/>
                
                <b>13.3. Indemnidad:</b> El FRANQUICIADO mantendrá indemne al FRANQUICIADOR de 
                cualquier reclamación derivada de la operación del Hotel."""
            }
        ]
        
        # Añadir cláusulas
        for clause in franchise_clauses:
            story.append(Paragraph(clause["title"], self.styles['ClauseTitle']))
            story.append(Paragraph(clause["content"], self.styles['Justified']))
        
        # Confidencialidad final
        story.append(Paragraph("DECIMOCUARTA.- CONFIDENCIALIDAD Y PROPIEDAD INTELECTUAL", self.styles['ClauseTitle']))
        confidential_text = """Las partes mantendrán estricta confidencialidad sobre el know-how, 
        información comercial y financiera intercambiada. Esta obligación sobrevivirá 5 años a la 
        terminación del contrato.<br/><br/>
        
        Todo el material, manuales, sistemas y procedimientos seguirán siendo propiedad exclusiva 
        del FRANQUICIADOR."""
        story.append(Paragraph(confidential_text, self.styles['Justified']))
        
        # Ley y jurisdicción
        story.append(Paragraph("DECIMOQUINTA.- LEY APLICABLE Y JURISDICCIÓN", self.styles['ClauseTitle']))
        law_text = """Este contrato se regirá por las leyes españolas. Para cualquier controversia, 
        las partes se someten a los Juzgados y Tribunales de Barcelona, renunciando a cualquier 
        otro fuero que pudiera corresponderles."""
        story.append(Paragraph(law_text, self.styles['Justified']))
        
        # Firmas
        story.append(PageBreak())
        story.append(Spacer(1, 1*inch))
        
        firma_text = """Y en prueba de conformidad, las partes firman el presente contrato por 
        triplicado y a un solo efecto, en el lugar y fecha indicados en el encabezamiento."""
        story.append(Paragraph(firma_text, self.styles['Justified']))
        story.append(Spacer(1, 1*inch))
        
        # Tabla de firmas
        firma_data = [
            ["EL FRANQUICIADOR", "EL FRANQUICIADO"],
            ["", ""],
            ["", ""],
            ["_" * 40, "_" * 40],
            ["Dña. Ana María Barceló Tous", "D. Josep Puig i Cadafalch"],
            ["BARCELÓ HOTEL GROUP, S.A.", "COSTA BRAVA RESORTS, S.L."]
        ]
        
        firma_table = Table(firma_data, colWidths=[3.5*inch, 3.5*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 2), (-1, 2), 50),
        ]))
        
        story.append(firma_table)
        
        # Generar PDF
        doc.build(story)
        print(f"✅ Generado: {filename}")
        
    def generate_lease_contract(self):
        """Genera contrato de arrendamiento de local"""
        filename = "contrato_arrendamiento_local_BHG.pdf"
        doc = SimpleDocTemplate(
            str(self.output_dir / filename),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        story = []
        
        # Título
        story.append(Paragraph("CONTRATO DE ARRENDAMIENTO DE LOCAL DE NEGOCIO", self.styles['ContractTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Contenido
        intro = """En Sevilla, a 10 de abril de 2024.<br/><br/>
        
        <b>REUNIDOS</b><br/><br/>
        
        De una parte, <b>INMOBILIARIA BARCELÓ, S.L.</b>, con CIF B-07123456, domiciliada en 
        Calle José Rover Motta, 27, Palma de Mallorca, representada por D. Francisco Javier 
        Barceló Martín, en calidad de Apoderado (en adelante, el <b>"ARRENDADOR"</b>).<br/><br/>
        
        De otra parte, <b>GASTRONOMY EXCELLENCE GROUP, S.L.</b>, con CIF B-41987654, domiciliada 
        en Calle Sierpes, 45, Sevilla, representada por Dña. Isabel Domínguez Pérez, en calidad 
        de Administradora Única (en adelante, el <b>"ARRENDATARIO"</b>).<br/><br/>
        
        <b>EXPONEN</b><br/><br/>
        
        I. Que el ARRENDADOR es propietario del local comercial situado en la planta baja del 
        Hotel Barceló Sevilla Renacimiento, con entrada independiente por Avenida Álvaro Alonso 
        Barba, número 15, con una superficie de 450 m² útiles.<br/><br/>
        
        II. Que el ARRENDATARIO está interesado en arrendar dicho local para destinarlo a 
        restaurante de alta gastronomía.<br/><br/>
        
        III. Que ambas partes han acordado formalizar el presente contrato de arrendamiento de 
        local de negocio, que se regirá por las siguientes <b>CLÁUSULAS</b>:"""
        
        story.append(Paragraph(intro, self.styles['Justified']))
        
        # Cláusulas del arrendamiento
        lease_clauses = [
            {
                "title": "PRIMERA.- OBJETO",
                "content": """El ARRENDADOR cede en arrendamiento al ARRENDATARIO, que acepta, el local 
                comercial descrito en los expositivos, con los siguientes elementos:<br/><br/>
                
                - Superficie útil: 450 m²<br/>
                - Superficie terraza exterior: 120 m²<br/>
                - Aforo máximo autorizado: 180 personas<br/>
                - Licencia de actividad: Restaurante con música<br/>
                - Instalaciones: Cocina equipada, sistema climatización, extractores<br/>
                - 2 plazas de aparcamiento en sótano<br/><br/>
                
                El local se entrega en perfecto estado de uso y conservación, totalmente terminado 
                y con todas las instalaciones en funcionamiento."""
            },
            {
                "title": "SEGUNDA.- DESTINO",
                "content": """<b>2.1.</b> El local se destinará exclusivamente a restaurante de alta 
                gastronomía, con posibilidad de servicio de catering exterior.<br/><br/>
                
                <b>2.2.</b> Queda expresamente prohibido:<br/>
                - Cambiar el destino sin autorización escrita<br/>
                - Actividades molestas, insalubres o peligrosas<br/>
                - Almacenaje de mercancías peligrosas<br/>
                - Subarrendar total o parcialmente<br/><br/>
                
                <b>2.3.</b> El horario máximo de apertura será hasta las 2:00 AM, respetando 
                la normativa municipal y las ordenanzas del hotel."""
            },
            {
                "title": "TERCERA.- DURACIÓN",
                "content": """<b>3.1.</b> El contrato tendrá una duración de <b>DIEZ (10) AÑOS</b>, 
                comenzando el 1 de mayo de 2024 y finalizando el 30 de abril de 2034.<br/><br/>
                
                <b>3.2.</b> Transcurridos los primeros 5 años, el contrato será de prórroga obligatoria 
                para el ARRENDADOR por períodos anuales hasta completar los 10 años, salvo que el 
                ARRENDATARIO manifieste su voluntad de no renovar con 4 meses de antelación.<br/><br/>
                
                <b>3.3.</b> Finalizado el plazo, el contrato podrá prorrogarse por mutuo acuerdo 
                en las condiciones que las partes pacten."""
            },
            {
                "title": "CUARTA.- RENTA Y ACTUALIZACIÓN",
                "content": """<b>4.1. Renta Fija:</b> OCHO MIL EUROS (8.000€) mensuales más IVA durante 
                el primer año.<br/><br/>
                
                <b>4.2. Renta Variable:</b> Adicionalmente, cuando la facturación mensual supere los 
                80.000€, el ARRENDATARIO abonará un 5% de la facturación que exceda dicha cantidad.<br/><br/>
                
                <b>4.3. Actualización:</b> La renta fija se actualizará anualmente según el IPC 
                publicado por el INE, con un mínimo del 2% y un máximo del 4%.<br/><br/>
                
                <b>4.4. Gastos Incluidos:</b> La renta incluye el IBI. Los suministros (agua, luz, 
                gas) y demás gastos serán por cuenta del ARRENDATARIO."""
            },
            {
                "title": "QUINTA.- FORMA DE PAGO",
                "content": """<b>5.1.</b> La renta se abonará por meses anticipados, dentro de los 
                primeros 5 días de cada mes, mediante transferencia bancaria a la cuenta designada 
                por el ARRENDADOR.<br/><br/>
                
                <b>5.2.</b> La renta variable se liquidará trimestralmente, presentando el ARRENDATARIO 
                declaración jurada de facturación junto con copia de las declaraciones fiscales.<br/><br/>
                
                <b>5.3.</b> El retraso en el pago devengará un interés de demora del 10% anual, 
                sin perjuicio del derecho del ARRENDADOR a resolver el contrato.<br/><br/>
                
                <b>5.4.</b> Todos los recibos incluirán el IVA correspondiente al tipo vigente."""
            },
            {
                "title": "SEXTA.- FIANZA Y GARANTÍAS",
                "content": """<b>6.1. Fianza Legal:</b> El ARRENDATARIO deposita en este acto fianza 
                equivalente a DOS (2) mensualidades de renta (16.000€), que será devuelta al 
                finalizar el contrato, previa verificación del estado del local.<br/><br/>
                
                <b>6.2. Garantía Adicional:</b> Aval bancario por importe de SEIS (6) meses de 
                renta (48.000€), ejecutable a primer requerimiento.<br/><br/>
                
                <b>6.3. Seguro de Impago:</b> El ARRENDATARIO contratará y mantendrá vigente un 
                seguro de impago de rentas a favor del ARRENDADOR.<br/><br/>
                
                <b>6.4. Actualización:</b> La fianza se actualizará cada 5 años conforme a la 
                renta actualizada."""
            },
            {
                "title": "SÉPTIMA.- OBRAS Y MEJORAS",
                "content": """<b>7.1. Obras de Adaptación:</b> El ARRENDATARIO podrá realizar las obras 
                de adaptación necesarias, previa autorización escrita del ARRENDADOR y obtención 
                de licencias.<br/><br/>
                
                <b>7.2. Obras de Conservación:</b> Serán por cuenta del ARRENDATARIO las reparaciones 
                necesarias para mantener el local en buen estado, salvo las estructurales.<br/><br/>
                
                <b>7.3. Mejoras:</b> Las mejoras fijas quedarán en beneficio de la propiedad sin 
                indemnización, salvo pacto contrario.<br/><br/>
                
                <b>7.4. Restitución:</b> Al finalizar, el ARRENDATARIO devolverá el local en el 
                estado en que lo recibió, salvo el desgaste por uso normal."""
            },
            {
                "title": "OCTAVA.- GASTOS Y SERVICIOS",
                "content": """<b>8.1. Por cuenta del ARRENDATARIO:</b><br/>
                - Suministros: agua, luz, gas, teléfono, internet<br/>
                - Tasa de basuras y alcantarillado<br/>
                - Gastos de comunidad: 350€/mes<br/>
                - Mantenimiento de sus instalaciones<br/>
                - Seguro de contenido y RC<br/><br/>
                
                <b>8.2. Por cuenta del ARRENDADOR:</b><br/>
                - IBI (incluido en la renta)<br/>
                - Seguro del continente<br/>
                - Reparaciones estructurales<br/><br/>
                
                <b>8.3. Lectura de Contadores:</b> Se realizará lectura mensual de consumos."""
            },
            {
                "title": "NOVENA.- SEGUROS",
                "content": """<b>9.1. Seguro de RC:</b> El ARRENDATARIO mantendrá seguro de RC con 
                cobertura mínima de 1.200.000€ por siniestro.<br/><br/>
                
                <b>9.2. Seguro de Contenido:</b> Asegurará el contenido, mobiliario y existencias 
                por su valor real.<br/><br/>
                
                <b>9.3. Seguro de Pérdida de Beneficios:</b> Recomendado pero no obligatorio.<br/><br/>
                
                <b>9.4. Beneficiario:</b> En las pólizas constará como beneficiario subsidiario 
                el ARRENDADOR para daños al local."""
            },
            {
                "title": "DÉCIMA.- TRASPASO Y SUBARRIENDO",
                "content": """<b>10.1. Prohibición:</b> Queda prohibido el subarriendo total o parcial 
                y la cesión del contrato sin consentimiento escrito del ARRENDADOR.<br/><br/>
                
                <b>10.2. Traspaso:</b> El ARRENDATARIO podrá traspasar el local transcurridos 3 años, 
                comunicándolo fehacientemente al ARRENDADOR con 2 meses de antelación.<br/><br/>
                
                <b>10.3. Participación:</b> El ARRENDADOR tendrá derecho al 20% del precio del 
                traspaso.<br/><br/>
                
                <b>10.4. Requisitos del Cesionario:</b> Deberá acreditar solvencia y experiencia 
                en hostelería."""
            },
            {
                "title": "UNDÉCIMA.- RESOLUCIÓN",
                "content": """Serán causas de resolución:<br/><br/>
                
                a) El impago de la renta o cantidades asimiladas<br/>
                b) El impago de la fianza o su actualización<br/>
                c) Destinar el local a uso distinto del pactado<br/>
                d) Realizar obras no consentidas<br/>
                e) El subarriendo o cesión inconsentidos<br/>
                f) Causar daños dolosos o negligentes graves<br/>
                g) Desarrollar actividades molestas, insalubres o ilícitas<br/>
                h) El cierre injustificado por más de 30 días<br/>
                i) La pérdida de licencias necesarias<br/>
                j) El incumplimiento grave de cualquier obligación"""
            },
            {
                "title": "DUODÉCIMA.- DERECHO DE ADQUISICIÓN PREFERENTE",
                "content": """<b>12.1. Tanteo:</b> El ARRENDATARIO tendrá derecho de tanteo en caso de 
                venta del local, debiendo el ARRENDADOR notificar fehacientemente las condiciones 
                de la venta proyectada.<br/><br/>
                
                <b>12.2. Plazo:</b> El ARRENDATARIO dispondrá de 30 días naturales para ejercitar 
                su derecho.<br/><br/>
                
                <b>12.3. Retracto:</b> Si se incumpliera el tanteo, el ARRENDATARIO podrá ejercitar 
                el retracto en los términos legales."""
            },
            {
                "title": "DECIMOTERCERA.- RESPONSABILIDADES",
                "content": """<b>13.1.</b> El ARRENDATARIO responderá de todos los daños causados en 
                el local por él, sus empleados o clientes.<br/><br/>
                
                <b>13.2.</b> El ARRENDADOR no responderá de los daños por robo, incendio o cualquier 
                otro siniestro en el local.<br/><br/>
                
                <b>13.3.</b> El ARRENDATARIO mantendrá indemne al ARRENDADOR de cualquier reclamación 
                derivada de su actividad.<br/><br/>
                
                <b>13.4.</b> El ARRENDATARIO cumplirá toda la normativa aplicable, especialmente 
                la sanitaria, laboral y de seguridad."""
            },
            {
                "title": "DECIMOCUARTA.- RELACIÓN CON EL HOTEL",
                "content": """<b>14.1. Independencia:</b> El restaurante operará de forma independiente 
                del hotel, con entrada y servicios propios.<br/><br/>
                
                <b>14.2. Colaboración:</b> Se podrán establecer acuerdos de colaboración para:<br/>
                - Servicio de room service<br/>
                - Desayunos del hotel<br/>
                - Eventos y banquetes<br/>
                - Descuentos a huéspedes<br/><br/>
                
                <b>14.3. Imagen:</b> El ARRENDATARIO mantendrá una imagen y nivel de calidad acorde 
                con el hotel 5 estrellas.<br/><br/>
                
                <b>14.4. Horarios:</b> Respetará los horarios de descanso de los huéspedes."""
            },
            {
                "title": "DECIMOQUINTA.- DISPOSICIONES FINALES",
                "content": """<b>15.1. Notificaciones:</b> Las comunicaciones se realizarán en los 
                domicilios del encabezamiento por medio fehaciente.<br/><br/>
                
                <b>15.2. Anexos:</b> Forman parte integrante del contrato:<br/>
                - Anexo I: Inventario de instalaciones y equipamiento<br/>
                - Anexo II: Planos del local<br/>
                - Anexo III: Licencias y autorizaciones<br/>
                - Anexo IV: Reglamento de régimen interior<br/><br/>
                
                <b>15.3. Jurisdicción:</b> Las partes se someten a los Juzgados y Tribunales de 
                Sevilla.<br/><br/>
                
                <b>15.4. Elevación a Público:</b> Cualquiera de las partes podrá elevar a público 
                este contrato, siendo los gastos por mitad."""
            }
        ]
        
        # Añadir cláusulas
        for clause in lease_clauses:
            story.append(Paragraph(clause["title"], self.styles['ClauseTitle']))
            story.append(Paragraph(clause["content"], self.styles['Justified']))
        
        # Firmas
        story.append(PageBreak())
        
        firma_text = """Y para que conste, y en prueba de conformidad, las partes firman el 
        presente contrato por duplicado y a un solo efecto, en el lugar y fecha del encabezamiento."""
        story.append(Paragraph(firma_text, self.styles['Justified']))
        story.append(Spacer(1, 1*inch))
        
        # Tabla de firmas
        firma_data = [
            ["EL ARRENDADOR", "EL ARRENDATARIO"],
            ["", ""],
            ["", ""],
            ["_" * 40, "_" * 40],
            ["D. Francisco Javier Barceló Martín", "Dña. Isabel Domínguez Pérez"],
            ["INMOBILIARIA BARCELÓ, S.L.", "GASTRONOMY EXCELLENCE GROUP, S.L."]
        ]
        
        firma_table = Table(firma_data, colWidths=[3.5*inch, 3.5*inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 2), (-1, 2), 50),
        ]))
        
        story.append(firma_table)
        
        # Generar PDF
        doc.build(story)
        print(f"✅ Generado: {filename}")
        
    def generate_all_contracts(self):
        """Genera todos los contratos de prueba"""
        print("\n🏨 GENERADOR DE CONTRATOS DE PRUEBA PARA BHG RAG")
        print("=" * 50)
        print("Generando contratos en formato PDF...\n")
        
        try:
            # Generar cada tipo de contrato
            self.generate_hotel_management_contract()
            self.generate_service_contract()
            self.generate_franchise_contract()
            self.generate_lease_contract()
            
            print(f"\n✅ Todos los contratos generados en: {self.output_dir}")
            print("\nContratos creados:")
            for pdf in self.output_dir.glob("*.pdf"):
                print(f"  📄 {pdf.name}")
                
        except Exception as e:
            print(f"\n❌ Error generando contratos: {str(e)}")

# Script principal
if __name__ == "__main__":
# Verificar que reportlab esté instalado
    try:
        import reportlab
        print("✅ ReportLab instalado correctamente")
    except ImportError:
        print("❌ ReportLab no está instalado. Instalando...")
        import subprocess
        subprocess.check_call(["pip", "install", "reportlab"])
        print("✅ ReportLab instalado")
        
    # Generar contratos
    generator = ContractGenerator()
    generator.generate_all_contracts()
        
    print("\n📌 Próximos pasos:")
    print("1. Ejecuta la aplicación: streamlit run src/ui/streamlit_app.py")
    print("2. Ve a la pestaña 'Documentos'")
    print("3. Carga los PDFs generados desde data/contracts")
    print("4. ¡Empieza a hacer preguntas sobre los contratos!")