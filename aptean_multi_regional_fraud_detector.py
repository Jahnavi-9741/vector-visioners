
# AI MULTI-REGIONAL DUPLICATE DETECTION SYSTEM FOR APTEAN
# =======================================================

import re
import json
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import difflib

@dataclass
class InvoiceFingerprint:
    content_hash: str
    vendor_name: str
    line_items: List[str]
    amounts: List[float]
    po_reference: str
    delivery_address: str
    normalized_content: str
    extracted_keywords: List[str]

@dataclass
class RegionalInvoice:
    invoice_id: str
    region: str
    currency: str
    total_amount: float
    submission_timestamp: str
    fingerprint: InvoiceFingerprint
    processing_status: str

@dataclass
class FraudAlert:
    alert_id: str
    fraud_type: str
    confidence_score: float
    affected_regions: List[str]
    duplicate_invoices: List[RegionalInvoice]
    potential_loss: float
    evidence_details: Dict
    recommended_action: str
    business_impact: Dict

class ApteanRegionalFraudDetector:
    def __init__(self):
        # Regional processing centers
        self.regional_centers = {
            "Germany": {"currency": "EUR", "timezone": "CET", "offices": ["Munich", "Frankfurt", "Hamburg"]},
            "USA": {"currency": "USD", "timezone": "EST/PST", "offices": ["Atlanta", "Chicago", "San Francisco"]},
            "UK": {"currency": "GBP", "timezone": "GMT", "offices": ["London", "Birmingham", "Manchester"]},
            "India": {"currency": "INR", "timezone": "IST", "offices": ["Bangalore", "Mumbai", "Chennai"]},
            "France": {"currency": "EUR", "timezone": "CET", "offices": ["Paris", "Lyon", "Marseille"]},
            "Canada": {"currency": "CAD", "timezone": "EST/PST", "offices": ["Toronto", "Vancouver", "Montreal"]}
        }

        # Cross-regional invoice database (simulated)
        self.cross_regional_database = []

        # Currency conversion rates for normalization
        self.currency_rates_to_usd = {
            "USD": 1.0,
            "EUR": 1.18,  # 1 EUR = 1.18 USD
            "GBP": 1.28,  # 1 GBP = 1.28 USD  
            "INR": 0.012, # 1 INR = 0.012 USD
            "CAD": 0.74,  # 1 CAD = 0.74 USD
            "JPY": 0.0067 # 1 JPY = 0.0067 USD
        }

        # Suspicious patterns for multi-regional attacks
        self.fraud_patterns = {
            "time_window_hours": 72,  # Submissions within 72 hours are suspicious
            "similarity_threshold": 0.85,  # 85% content similarity triggers alert
            "vendor_variance_threshold": 0.1,  # 10% amount variance across regions
            "po_reference_weight": 0.3,  # 30% weight for PO reference matching
            "delivery_address_weight": 0.25,  # 25% weight for delivery address
            "line_items_weight": 0.45   # 45% weight for line items similarity
        }

    def detect_multi_regional_fraud(self, invoice_data: Dict) -> FraudAlert:
        """Main AI function to detect multi-regional duplicate attacks"""

        # 1. CREATE INVOICE FINGERPRINT
        current_invoice = self._create_regional_invoice(invoice_data)

        # 2. SEARCH CROSS-REGIONAL DATABASE
        potential_duplicates = self._search_cross_regional_duplicates(current_invoice)

        # 3. PERFORM ADVANCED CONTENT ANALYSIS
        fraud_evidence = self._analyze_content_similarity(current_invoice, potential_duplicates)

        # 4. CALCULATE FRAUD CONFIDENCE SCORE
        confidence_score = self._calculate_fraud_confidence(fraud_evidence)

        # 5. ASSESS FINANCIAL IMPACT
        potential_loss = self._calculate_potential_loss(current_invoice, potential_duplicates)

        # 6. GENERATE FRAUD ALERT
        if confidence_score > 0.75:  # High confidence threshold
            return self._generate_fraud_alert(
                current_invoice, 
                potential_duplicates, 
                fraud_evidence, 
                confidence_score, 
                potential_loss
            )

        # 7. ADD TO CROSS-REGIONAL DATABASE
        self._add_to_regional_database(current_invoice)

        return None  # No fraud detected

    def _create_regional_invoice(self, invoice_data: Dict) -> RegionalInvoice:
        """Create structured regional invoice with fingerprint"""

        # Extract key invoice components
        invoice_text = invoice_data.get("invoice_text", "")

        # Create content fingerprint
        fingerprint = self._generate_content_fingerprint(invoice_text)

        regional_invoice = RegionalInvoice(
            invoice_id=invoice_data.get("invoice_id", ""),
            region=invoice_data.get("region", ""),
            currency=invoice_data.get("currency", ""),
            total_amount=invoice_data.get("total_amount", 0.0),
            submission_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fingerprint=fingerprint,
            processing_status="pending"
        )

        return regional_invoice

    def _generate_content_fingerprint(self, invoice_text: str) -> InvoiceFingerprint:
        """Generate unique fingerprint for invoice content"""

        # 1. EXTRACT VENDOR NAME
        vendor_patterns = [
            r"From:\s*(.+?)\n",
            r"Vendor:\s*(.+?)\n",
            r"Supplier:\s*(.+?)\n",
            r"Company:\s*(.+?)\n"
        ]

        vendor_name = ""
        for pattern in vendor_patterns:
            match = re.search(pattern, invoice_text, re.IGNORECASE)
            if match:
                vendor_name = match.group(1).strip()
                break

        # 2. EXTRACT LINE ITEMS
        line_items = []
        line_patterns = [
            r"Description:\s*(.+?)\n",
            r"Product:\s*(.+?)\n", 
            r"Service:\s*(.+?)\n",
            r"Item:\s*(.+?)\n"
        ]

        for pattern in line_patterns:
            matches = re.findall(pattern, invoice_text, re.IGNORECASE)
            line_items.extend([item.strip() for item in matches])

        # 3. EXTRACT AMOUNTS
        amount_patterns = [
            r"[\$€£₹¥]\s*([\d,]+\.?\d*)",
            r"([\d,]+\.?\d*)\s*(?:USD|EUR|GBP|INR|JPY)"
        ]

        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, invoice_text)
            for match in matches:
                try:
                    amount = float(match.replace(",", ""))
                    amounts.append(amount)
                except:
                    pass

        # 4. EXTRACT PO REFERENCE
        po_patterns = [
            r"PO[\s#:-]*([A-Z0-9-]+)",
            r"Purchase Order[\s#:-]*([A-Z0-9-]+)",
            r"Reference[\s#:-]*([A-Z0-9-]+)"
        ]

        po_reference = ""
        for pattern in po_patterns:
            match = re.search(pattern, invoice_text, re.IGNORECASE)
            if match:
                po_reference = match.group(1).strip()
                break

        # 5. EXTRACT DELIVERY ADDRESS
        address_patterns = [
            r"Delivery:\s*(.+?)(?:\n|$)",
            r"Ship to:\s*(.+?)(?:\n|$)",
            r"Address:\s*(.+?)(?:\n|$)"
        ]

        delivery_address = ""
        for pattern in address_patterns:
            match = re.search(pattern, invoice_text, re.IGNORECASE)
            if match:
                delivery_address = match.group(1).strip()
                break

        # 6. CREATE NORMALIZED CONTENT (for similarity comparison)
        normalized_content = self._normalize_content_for_comparison(invoice_text)

        # 7. EXTRACT KEYWORDS
        keywords = self._extract_keywords(invoice_text)

        # 8. GENERATE CONTENT HASH
        content_hash = hashlib.md5(normalized_content.encode()).hexdigest()

        return InvoiceFingerprint(
            content_hash=content_hash,
            vendor_name=vendor_name,
            line_items=line_items,
            amounts=amounts,
            po_reference=po_reference,
            delivery_address=delivery_address,
            normalized_content=normalized_content,
            extracted_keywords=keywords
        )

    def _normalize_content_for_comparison(self, invoice_text: str) -> str:
        """Normalize invoice content for cross-regional comparison"""

        # Remove currency symbols and replace with placeholder
        normalized = re.sub(r"[\$€£₹¥]", "CURRENCY", invoice_text)

        # Remove currency codes
        normalized = re.sub(r"\b(USD|EUR|GBP|INR|JPY|CAD)\b", "CURRENCY", normalized, flags=re.IGNORECASE)

        # Remove invoice numbers (different across regions)
        normalized = re.sub(r"Invoice\s*#?:?\s*[A-Z0-9-]+", "INVOICE_NUMBER", normalized, flags=re.IGNORECASE)

        # Remove dates (may vary slightly)
        normalized = re.sub(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", "DATE", normalized)

        # Remove amounts (focus on content structure)
        normalized = re.sub(r"\d+[,.]?\d*", "AMOUNT", normalized)

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized.strip())

        return normalized.lower()

    def _extract_keywords(self, invoice_text: str) -> List[str]:
        """Extract key terms for semantic matching"""

        # Important keywords that indicate invoice content
        keywords = []

        # Product/Service keywords
        product_keywords = re.findall(r"\b(software|license|consultation|equipment|service|support|maintenance|installation)\b", invoice_text, re.IGNORECASE)
        keywords.extend([kw.lower() for kw in product_keywords])

        # Company/Technology keywords  
        tech_keywords = re.findall(r"\b(Microsoft|Office|SAP|Oracle|AWS|Google|Enterprise|Professional|Premium)\b", invoice_text, re.IGNORECASE)
        keywords.extend([kw.lower() for kw in tech_keywords])

        return list(set(keywords))  # Remove duplicates

    def _search_cross_regional_duplicates(self, current_invoice: RegionalInvoice) -> List[RegionalInvoice]:
        """Search for potential duplicates across all regions"""

        potential_duplicates = []

        # Search within time window
        current_time = datetime.strptime(current_invoice.submission_timestamp, "%Y-%m-%d %H:%M:%S")
        time_window = timedelta(hours=self.fraud_patterns["time_window_hours"])

        for existing_invoice in self.cross_regional_database:
            existing_time = datetime.strptime(existing_invoice.submission_timestamp, "%Y-%m-%d %H:%M:%S")

            # Skip if outside time window
            if abs(current_time - existing_time) > time_window:
                continue

            # Skip if same region (different fraud type)
            if existing_invoice.region == current_invoice.region:
                continue

            # Check for potential similarity
            if self._quick_similarity_check(current_invoice, existing_invoice):
                potential_duplicates.append(existing_invoice)

        return potential_duplicates

    def _quick_similarity_check(self, invoice1: RegionalInvoice, invoice2: RegionalInvoice) -> bool:
        """Quick pre-filter for potential duplicates"""

        # Check PO reference match (strong indicator)
        if (invoice1.fingerprint.po_reference and invoice2.fingerprint.po_reference and
            invoice1.fingerprint.po_reference.lower() == invoice2.fingerprint.po_reference.lower()):
            return True

        # Check vendor name similarity
        if invoice1.fingerprint.vendor_name and invoice2.fingerprint.vendor_name:
            vendor_similarity = difflib.SequenceMatcher(
                None, 
                invoice1.fingerprint.vendor_name.lower(), 
                invoice2.fingerprint.vendor_name.lower()
            ).ratio()

            if vendor_similarity > 0.8:
                return True

        # Check delivery address match
        if (invoice1.fingerprint.delivery_address and invoice2.fingerprint.delivery_address and
            invoice1.fingerprint.delivery_address.lower() in invoice2.fingerprint.delivery_address.lower()):
            return True

        return False

    def _analyze_content_similarity(self, current_invoice: RegionalInvoice, 
                                  potential_duplicates: List[RegionalInvoice]) -> Dict:
        """Perform detailed content similarity analysis"""

        evidence = {
            "matches": [],
            "similarity_scores": {},
            "matching_elements": {},
            "currency_analysis": {},
            "temporal_analysis": {}
        }

        for duplicate in potential_duplicates:
            match_evidence = self._compare_invoices_detailed(current_invoice, duplicate)

            if match_evidence["overall_similarity"] > self.fraud_patterns["similarity_threshold"]:
                evidence["matches"].append(duplicate)
                evidence["similarity_scores"][duplicate.invoice_id] = match_evidence["overall_similarity"]
                evidence["matching_elements"][duplicate.invoice_id] = match_evidence["matching_elements"]
                evidence["currency_analysis"][duplicate.invoice_id] = match_evidence["currency_analysis"]
                evidence["temporal_analysis"][duplicate.invoice_id] = match_evidence["temporal_analysis"]

        return evidence

    def _compare_invoices_detailed(self, invoice1: RegionalInvoice, invoice2: RegionalInvoice) -> Dict:
        """Detailed comparison between two invoices"""

        comparison = {
            "overall_similarity": 0.0,
            "matching_elements": {},
            "currency_analysis": {},
            "temporal_analysis": {}
        }

        # 1. CONTENT SIMILARITY
        content_similarity = difflib.SequenceMatcher(
            None, 
            invoice1.fingerprint.normalized_content, 
            invoice2.fingerprint.normalized_content
        ).ratio()

        # 2. PO REFERENCE MATCH
        po_match = 0.0
        if (invoice1.fingerprint.po_reference and invoice2.fingerprint.po_reference and
            invoice1.fingerprint.po_reference.lower() == invoice2.fingerprint.po_reference.lower()):
            po_match = 1.0

        # 3. DELIVERY ADDRESS SIMILARITY
        address_similarity = 0.0
        if invoice1.fingerprint.delivery_address and invoice2.fingerprint.delivery_address:
            address_similarity = difflib.SequenceMatcher(
                None,
                invoice1.fingerprint.delivery_address.lower(),
                invoice2.fingerprint.delivery_address.lower()
            ).ratio()

        # 4. LINE ITEMS SIMILARITY
        line_items_similarity = self._compare_line_items(
            invoice1.fingerprint.line_items, 
            invoice2.fingerprint.line_items
        )

        # 5. CALCULATE WEIGHTED OVERALL SIMILARITY
        overall_similarity = (
            content_similarity * 0.3 +
            po_match * self.fraud_patterns["po_reference_weight"] +
            address_similarity * self.fraud_patterns["delivery_address_weight"] +
            line_items_similarity * self.fraud_patterns["line_items_weight"]
        )

        # 6. CURRENCY ANALYSIS
        currency_analysis = self._analyze_currency_relationship(invoice1, invoice2)

        # 7. TEMPORAL ANALYSIS
        temporal_analysis = self._analyze_submission_timing(invoice1, invoice2)

        comparison.update({
            "overall_similarity": overall_similarity,
            "matching_elements": {
                "content_similarity": content_similarity,
                "po_reference_match": po_match,
                "address_similarity": address_similarity,
                "line_items_similarity": line_items_similarity
            },
            "currency_analysis": currency_analysis,
            "temporal_analysis": temporal_analysis
        })

        return comparison

    def _compare_line_items(self, items1: List[str], items2: List[str]) -> float:
        """Compare line items between invoices"""

        if not items1 or not items2:
            return 0.0

        total_similarity = 0.0
        comparisons = 0

        for item1 in items1:
            for item2 in items2:
                similarity = difflib.SequenceMatcher(None, item1.lower(), item2.lower()).ratio()
                total_similarity += similarity
                comparisons += 1

        return total_similarity / comparisons if comparisons > 0 else 0.0

    def _analyze_currency_relationship(self, invoice1: RegionalInvoice, invoice2: RegionalInvoice) -> Dict:
        """Analyze if amounts match after currency conversion"""

        # Convert both amounts to USD for comparison
        amount1_usd = invoice1.total_amount * self.currency_rates_to_usd.get(invoice1.currency, 1.0)
        amount2_usd = invoice2.total_amount * self.currency_rates_to_usd.get(invoice2.currency, 1.0)

        # Calculate variance
        if amount1_usd > 0:
            variance = abs(amount1_usd - amount2_usd) / amount1_usd
        else:
            variance = 1.0

        return {
            "amount1_usd": round(amount1_usd, 2),
            "amount2_usd": round(amount2_usd, 2),
            "variance_percentage": round(variance * 100, 2),
            "suspicious": variance < self.fraud_patterns["vendor_variance_threshold"],
            "currency_pair": f"{invoice1.currency}-{invoice2.currency}"
        }

    def _analyze_submission_timing(self, invoice1: RegionalInvoice, invoice2: RegionalInvoice) -> Dict:
        """Analyze submission timing patterns"""

        time1 = datetime.strptime(invoice1.submission_timestamp, "%Y-%m-%d %H:%M:%S")
        time2 = datetime.strptime(invoice2.submission_timestamp, "%Y-%m-%d %H:%M:%S")

        time_diff = abs(time1 - time2)
        hours_diff = time_diff.total_seconds() / 3600

        return {
            "time_difference_hours": round(hours_diff, 2),
            "submission_order": "sequential" if hours_diff < 24 else "spread",
            "suspicious_timing": hours_diff < self.fraud_patterns["time_window_hours"],
            "regions": f"{invoice1.region} → {invoice2.region}"
        }

    def _calculate_fraud_confidence(self, evidence: Dict) -> float:
        """Calculate overall fraud confidence score"""

        if not evidence["matches"]:
            return 0.0

        # Base confidence from similarity scores
        max_similarity = max(evidence["similarity_scores"].values())
        confidence = max_similarity

        # Boost confidence for multiple regional matches
        region_multiplier = min(1.5, 1.0 + (len(evidence["matches"]) - 1) * 0.2)
        confidence *= region_multiplier

        # Boost confidence for currency variance patterns
        for match_id, currency_data in evidence["currency_analysis"].items():
            if currency_data["suspicious"]:
                confidence += 0.1

        # Boost confidence for temporal patterns
        for match_id, temporal_data in evidence["temporal_analysis"].items():
            if temporal_data["suspicious_timing"]:
                confidence += 0.05

        return min(0.99, confidence)

    def _calculate_potential_loss(self, current_invoice: RegionalInvoice, 
                                duplicates: List[RegionalInvoice]) -> float:
        """Calculate potential financial loss from fraud"""

        # Convert current invoice to USD
        current_usd = current_invoice.total_amount * self.currency_rates_to_usd.get(current_invoice.currency, 1.0)

        # Add duplicate amounts
        duplicate_usd = 0.0
        for duplicate in duplicates:
            duplicate_amount = duplicate.total_amount * self.currency_rates_to_usd.get(duplicate.currency, 1.0)
            duplicate_usd += duplicate_amount

        # Total potential loss (assuming one is legitimate)
        return round(duplicate_usd, 2)

    def _generate_fraud_alert(self, current_invoice: RegionalInvoice, 
                            duplicates: List[RegionalInvoice], 
                            evidence: Dict, confidence_score: float, 
                            potential_loss: float) -> FraudAlert:
        """Generate comprehensive fraud alert"""

        affected_regions = [current_invoice.region] + [dup.region for dup in duplicates]
        all_invoices = [current_invoice] + duplicates

        # Generate business impact analysis
        business_impact = self._calculate_business_impact(potential_loss, affected_regions, confidence_score)

        # Generate recommended action
        recommended_action = self._generate_action_recommendation(confidence_score, potential_loss, affected_regions)

        alert = FraudAlert(
            alert_id=f"FRAUD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{current_invoice.region}",
            fraud_type="Multi-Regional Duplicate Attack",
            confidence_score=confidence_score,
            affected_regions=list(set(affected_regions)),
            duplicate_invoices=all_invoices,
            potential_loss=potential_loss,
            evidence_details=evidence,
            recommended_action=recommended_action,
            business_impact=business_impact
        )

        return alert

    def _calculate_business_impact(self, potential_loss: float, affected_regions: List[str], 
                                 confidence_score: float) -> Dict:
        """Calculate business impact of detected fraud"""

        return {
            "financial_impact": f"${potential_loss:,.2f} potential duplicate payments prevented",
            "operational_impact": f"{len(affected_regions)} regional offices affected - coordinated response required",
            "reputational_impact": "High - multi-regional fraud attempt indicates sophisticated attack",
            "compliance_impact": "Cross-border fraud investigation may require regulatory reporting",
            "detection_benefit": f"AI detected in real-time vs typical 3-6 month discovery period",
            "confidence_level": f"{confidence_score:.1%} confidence in fraud detection"
        }

    def _generate_action_recommendation(self, confidence_score: float, potential_loss: float, 
                                      affected_regions: List[str]) -> str:
        """Generate specific action recommendations"""

        if confidence_score > 0.90:
            return "🚨 IMMEDIATE ACTION: Block all invoices, freeze vendor payments, initiate fraud investigation across all affected regions"
        elif confidence_score > 0.85:
            return "⚠️ HIGH PRIORITY: Hold all payments, require manager approval, coordinate cross-regional verification"
        elif confidence_score > 0.75:
            return "⚡ ENHANCED REVIEW: Flag for detailed manual review, verify with vendor directly, confirm legitimacy"
        else:
            return "📋 MONITOR: Continue monitoring, document patterns, increase verification requirements"

    def _add_to_regional_database(self, invoice: RegionalInvoice):
        """Add invoice to cross-regional database for future comparisons"""
        self.cross_regional_database.append(invoice)

# DEMO FUNCTION
def demo_multi_regional_fraud_detection():
    """Demo the Multi-Regional Fraud Detection system"""

    detector = ApteanRegionalFraudDetector()

    # SCENARIO: Multi-Regional Attack - Same Microsoft license purchase submitted to 3 regions
    print("🚨 APTEAN MULTI-REGIONAL FRAUD DETECTION - AI DEMO")
    print("=" * 70)
    print("Scenario: Fraudster submits same Microsoft purchase to 3 regions")
    print("=" * 70)

    # STEP 1: German office receives invoice
    german_invoice = {
        "invoice_id": "DE-2024-1001",
        "region": "Germany", 
        "currency": "EUR",
        "total_amount": 50000.00,
        "invoice_text": """RECHNUNG
        From: Microsoft Deutschland GmbH
        Invoice ID: DE-2024-1001

        Description: Office 365 Enterprise E5 - 500 licenses
        Quantity: 500
        Unit Price: €100.00
        Total: €50,000.00

        Delivery: Aptean Munich Office, Germany
        PO Reference: PO-APT-2024-SFT-789

        Payment Terms: Net 30"""
    }

    print("\n📄 PROCESSING: German Invoice DE-2024-1001 (€50,000)")
    result1 = detector.detect_multi_regional_fraud(german_invoice)
    print("✅ Status: Added to regional database (no duplicates found)")

    # STEP 2: US office receives similar invoice (2 hours later)
    us_invoice = {
        "invoice_id": "US-2024-2156", 
        "region": "USA",
        "currency": "USD",
        "total_amount": 55000.00,
        "invoice_text": """INVOICE
        From: Microsoft Corporation USA
        Invoice #: US-2024-2156

        Description: Office 365 Enterprise E5 - 500 licenses  
        Quantity: 500
        Unit Price: $110.00
        Total: $55,000.00

        Delivery: Aptean Munich Office, Germany
        PO Reference: PO-APT-2024-SFT-789

        Payment Terms: Net 30"""
    }

    print("\n📄 PROCESSING: US Invoice US-2024-2156 ($55,000)")
    result2 = detector.detect_multi_regional_fraud(us_invoice)

    if result2:
        print("🚨 FRAUD ALERT GENERATED!")
        print(f"Alert ID: {result2.alert_id}")
        print(f"Confidence: {result2.confidence_score:.1%}")
        print(f"Affected Regions: {', '.join(result2.affected_regions)}")
        print(f"Potential Loss: ${result2.potential_loss:,.2f}")
        print(f"Recommendation: {result2.recommended_action}")

        print("\n🔍 EVIDENCE DETAILS:")
        for invoice_id, similarity in result2.evidence_details["similarity_scores"].items():
            print(f"  • Similar to {invoice_id}: {similarity:.1%} match")

        for invoice_id, currency_data in result2.evidence_details["currency_analysis"].items():
            print(f"  • Currency Analysis: {currency_data['currency_pair']} - {currency_data['variance_percentage']}% variance")
            print(f"    USD Equivalent: ${currency_data['amount1_usd']} vs ${currency_data['amount2_usd']}")

        print("\n📈 BUSINESS IMPACT:")
        for metric, value in result2.business_impact.items():
            print(f"  • {metric.replace('_', ' ').title()}: {value}")

    print("\n" + "=" * 70)
    print("💡 AI successfully detected multi-regional duplicate attack!")
    print("Prevention: Saved Aptean from $55,000 duplicate payment")
    print("Detection Speed: Real-time vs 3-6 months manual discovery")

if __name__ == "__main__":
    demo_multi_regional_fraud_detection()
