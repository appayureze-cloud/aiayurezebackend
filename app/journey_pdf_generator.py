"""
Journey PDF Report Generator
Creates comprehensive PDF reports for patients and admins with app branding
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO

from .companion_system import companion_manager
from .journey_rating_system import rating_system
from .database_models import SessionLocal, PrescriptionRecord, PrescribedMedicine, PatientProfile

logger = logging.getLogger(__name__)

class JourneyPDFGenerator:
    """Generates comprehensive PDF reports for patient journeys"""
    
    def __init__(self):
        self.brand_color = colors.Color(0.133, 0.545, 0.133)  # Forest green for Ayurveda
        self.light_green = colors.Color(0.9, 0.98, 0.9)
        
    async def generate_patient_report(
        self,
        journey_id: str,
        case_id: str
    ) -> Optional[bytes]:
        """
        Generate comprehensive journey report for patient
        
        Includes:
        - Journey summary
        - Treatment progress
        - Medicine adherence
        - Milestones achieved
        - Final rating & feedback
        """
        try:
            logger.info(f"📄 Generating patient report for journey: {journey_id}")
            
            # Get journey data
            journey = await companion_manager.get_journey(journey_id)
            if not journey:
                logger.error(f"Journey not found: {journey_id}")
                return None
            
            # Get case data
            case = await companion_manager.get_case(case_id)
            if not case:
                logger.error(f"Case not found: {case_id}")
                return None
            
            # Get rating data
            rating = rating_system.get_rating(journey_id)
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=self.brand_color,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=self.brand_color,
                spaceBefore=20,
                spaceAfter=10
            )
            
            # Header with logo
            story.append(Paragraph("🌿 AyurEze Healthcare", title_style))
            story.append(Paragraph("Your AI Wellness Journey Report", styles['Heading3']))
            story.append(Spacer(1, 0.3*inch))
            
            # Journey Summary Section
            story.append(Paragraph("📊 Journey Summary", heading_style))
            
            journey_data = [
                ["Journey ID:", journey_id[:16] + "..."],
                ["Case ID:", case_id[:16] + "..."],
                ["Health Concern:", journey['health_concern']],
                ["Status:", journey['status'].upper()],
                ["Started:", journey['started_at'][:10]],
                ["Duration:", f"{case['treatment_duration_days']} days"],
                ["Total Interactions:", str(journey['interaction_count'])],
            ]
            
            journey_table = Table(journey_data, colWidths=[2*inch, 4*inch])
            journey_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_green),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(journey_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Treatment Progress Section
            story.append(Paragraph("📈 Treatment Progress", heading_style))
            
            progress_data = [
                ["Overall Progress:", f"{case['progress_percentage']}%"],
                ["Adherence Score:", f"{case['adherence_score']}%"],
                ["Diagnosis:", case['diagnosis']],
                ["Treatment Status:", case['status'].upper()],
            ]
            
            progress_table = Table(progress_data, colWidths=[2*inch, 4*inch])
            progress_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), self.light_green),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(progress_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Milestones Achieved
            if journey.get('milestones_achieved'):
                story.append(Paragraph("🏆 Milestones Achieved", heading_style))
                for i, milestone in enumerate(journey['milestones_achieved'], 1):
                    story.append(Paragraph(f"✅ {i}. {milestone}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Rating & Feedback Section
            if rating:
                story.append(Paragraph("⭐ Your Feedback", heading_style))
                
                rating_data = [
                    ["Overall Rating:", "⭐" * rating.rating],
                    ["Symptom Improvement:", f"{rating.symptom_improvement}%"],
                    ["Companion Helpfulness:", "⭐" * rating.companion_helpfulness],
                    ["Reminder Effectiveness:", "⭐" * rating.reminder_effectiveness],
                    ["Would Recommend:", "Yes ✅" if rating.would_recommend else "No ❌"],
                ]
                
                rating_table = Table(rating_data, colWidths=[2.5*inch, 3.5*inch])
                rating_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), self.light_green),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('PADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(rating_table)
                
                if rating.feedback_text:
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(f"<b>Feedback:</b> {rating.feedback_text}", styles['Normal']))
                
                story.append(Spacer(1, 0.3*inch))
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_text = """
            <para align=center>
            <b>🌿 Thank You for Trusting AyurEze Healthcare 🌿</b><br/>
            Your wellness is our priority. Stay healthy!<br/>
            <i>Generated by Astra AI Wellness Companion</i><br/>
            Report Date: {}<br/>
            </para>
            """.format(datetime.now().strftime("%B %d, %Y"))
            story.append(Paragraph(footer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"✅ Patient report generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating patient report: {e}", exc_info=True)
            return None
    
    async def generate_admin_report(
        self,
        journey_id: str,
        case_id: str
    ) -> Optional[bytes]:
        """
        Generate detailed admin report
        
        Includes:
        - All patient data
        - Detailed intervention logs
        - Prescription details
        - Medicine schedule
        - Analytics
        """
        try:
            logger.info(f"📄 Generating admin report for journey: {journey_id}")
            
            # Get all data
            journey = await companion_manager.get_journey(journey_id)
            case = await companion_manager.get_case(case_id)
            rating = rating_system.get_rating(journey_id)
            
            if not journey or not case:
                return None
            
            # Get prescription details from database
            prescription_id = case.get('prescription_id')
            prescription = None
            medicines = []
            
            if prescription_id:
                db = SessionLocal()
                try:
                    prescription = db.query(PrescriptionRecord).filter(
                        PrescriptionRecord.prescription_id == prescription_id
                    ).first()
                    
                    medicines = db.query(PrescribedMedicine).filter(
                        PrescribedMedicine.prescription_id == prescription_id
                    ).all()
                finally:
                    db.close()
            
            # Create comprehensive admin PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'AdminTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=self.brand_color,
                spaceAfter=20,
                alignment=TA_CENTER
            )
            
            story.append(Paragraph("🔐 ADMIN REPORT - CONFIDENTIAL", title_style))
            story.append(Paragraph("AyurEze Healthcare - Journey Analytics", styles['Heading3']))
            story.append(Spacer(1, 0.2*inch))
            
            # Journey Overview
            story.append(Paragraph("Journey Overview", styles['Heading2']))
            overview_data = [
                ["Journey ID", journey_id],
                ["Case ID", case_id],
                ["Patient ID", journey['user_id']],
                ["Doctor ID", case.get('doctor_id', 'N/A')],
                ["Health Concern", journey['health_concern']],
                ["Status", journey['status']],
                ["Created", journey['started_at']],
                ["Last Interaction", journey.get('last_interaction', 'N/A')],
                ["Total Interactions", str(journey['interaction_count'])],
            ]
            
            overview_table = Table(overview_data)
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(overview_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Treatment Details
            story.append(Paragraph("Treatment Details", styles['Heading2']))
            treatment_data = [
                ["Diagnosis", case['diagnosis']],
                ["Treatment Duration", f"{case['treatment_duration_days']} days"],
                ["Progress", f"{case['progress_percentage']}%"],
                ["Adherence Score", f"{case['adherence_score']}%"],
                ["Status", case['status']],
            ]
            
            treatment_table = Table(treatment_data)
            treatment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(treatment_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Prescribed Medicines
            if medicines:
                story.append(Paragraph("Prescribed Medicines", styles['Heading2']))
                med_data = [["Medicine", "Dose", "Schedule", "Duration"]]
                for med in medicines:
                    med_data.append([
                        med.medicine_name,
                        med.dose or "N/A",
                        med.schedule or "N/A",
                        med.duration or "N/A"
                    ])
                
                med_table = Table(med_data)
                med_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 4),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]))
                story.append(med_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Rating Summary
            if rating:
                story.append(Paragraph("Patient Feedback", styles['Heading2']))
                feedback_data = [
                    ["Overall Rating", f"{rating.rating}/5 stars"],
                    ["Symptom Improvement", f"{rating.symptom_improvement}%"],
                    ["Companion Helpfulness", f"{rating.companion_helpfulness}/5"],
                    ["Reminder Effectiveness", f"{rating.reminder_effectiveness}/5"],
                    ["Would Recommend", "Yes" if rating.would_recommend else "No"],
                    ["Feedback", rating.feedback_text or "None"],
                ]
                
                feedback_table = Table(feedback_data)
                feedback_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.brand_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(feedback_table)
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer = f"""
            <para align=center>
            <b>CONFIDENTIAL - FOR AUTHORIZED PERSONNEL ONLY</b><br/>
            Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br/>
            AyurEze Healthcare - Admin Dashboard<br/>
            </para>
            """
            story.append(Paragraph(footer, styles['Normal']))
            
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"✅ Admin report generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating admin report: {e}", exc_info=True)
            return None

# Global instance
pdf_generator = JourneyPDFGenerator()
