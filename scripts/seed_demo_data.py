"""Seed script for Dental Radar local usability testing.

Populates PostgreSQL with realistic clinics, locations, buying signals,
computed scores, and AI enrichment summaries.
"""

from datetime import UTC, datetime, timedelta
import sys
from uuid import uuid4

# Ensure backend package is in python path
from app.domain.entities.scoring_config import ScoringConfig
from app.domain.entities.signal import Signal
from app.domain.services.scoring_service import ScoringService
from app.domain.value_objects.signal_type import SignalType
from app.infrastructure.db.models import (
    ClinicModel,
    EnrichmentModel,
    LocationModel,
    ScoreModel,
    ScoringConfigModel,
    SignalModel,
)
from app.infrastructure.db.session import SessionLocal

SAMPLE_CLINICS = [
    {
        "name": "Clínica Dentária Avenida Premium",
        "place_id": "demo_place_01",
        "phone": "+351 21 345 6789",
        "website": "https://avenidadental.pt",
        "google_rating": 4.9,
        "google_review_count": 482,
        "locations_count": 3,
        "social_urls": ["https://instagram.com/avenidadental", "https://facebook.com/avenidadental"],
        "locations": [
            {
                "street": "Avenida da Liberdade 240, 3º",
                "city": "Lisboa",
                "state": "Lisboa",
                "postal_code": "1250-149",
                "country": "Portugal",
                "lat": 38.7223,
                "lng": -9.1493,
                "is_primary": True,
            },
            {
                "street": "Rua Castilho 52",
                "city": "Lisboa",
                "state": "Lisboa",
                "postal_code": "1250-071",
                "country": "Portugal",
                "lat": 38.7251,
                "lng": -9.1512,
                "is_primary": False,
            },
            {
                "street": "Avenida Marginal 820",
                "city": "Cascais",
                "state": "Lisboa",
                "postal_code": "2750-427",
                "country": "Portugal",
                "lat": 38.7001,
                "lng": -9.4180,
                "is_primary": False,
            },
        ],
        "signals": [
            (SignalType.HIRING, "Anúncio ativo de recrutamento no LinkedIn e portal da clínica para 2 Médicos Dentistas e 1 Higienista."),
            (SignalType.ADVERTISING, "Campanhas ativas no Google Ads e Meta Ads promovendo alinhadores invisíveis e implantes All-on-4."),
            (SignalType.WEBSITE_QUALITY, "Website moderno, responsivo, com agendamento online integrado e tempo de carregamento inferior a 1.2s."),
            (SignalType.MULTI_LOCATION, "3 unidades operacionais identificadas em Lisboa e Cascais com equipa partilhada."),
            (SignalType.HIGH_TICKET, "Destaque comercial para tratamentos de reabilitação oral total, facetas em cerâmica e cirurgia guiada por computador."),
        ],
        "enrichment": {
            "growth_probability": 94,
            "technology_maturity": 88,
            "marketing_sophistication": 92,
            "expansion_probability": 85,
            "explanation": (
                "Clínica de topo de gama com forte investimento em captação de clientes para procedimentos de alto valor. "
                "Presença ativa em 3 locais e contratação contínua indicam excelente potencial de aquisição de soluções premium."
            ),
        },
    },
    {
        "name": "Instituto de Implantologia e Estética do Norte",
        "place_id": "demo_place_02",
        "phone": "+351 22 609 8123",
        "website": "https://implantologianorte.pt",
        "google_rating": 4.8,
        "google_review_count": 315,
        "locations_count": 2,
        "social_urls": ["https://instagram.com/institutoimplantenorte"],
        "locations": [
            {
                "street": "Avenida da Boavista 1472",
                "city": "Porto",
                "state": "Porto",
                "postal_code": "4100-131",
                "country": "Portugal",
                "lat": 41.1579,
                "lng": -8.6291,
                "is_primary": True,
            },
            {
                "street": "Rua de Santa Catarina 310",
                "city": "Porto",
                "state": "Porto",
                "postal_code": "4000-443",
                "country": "Portugal",
                "lat": 41.1496,
                "lng": -8.6054,
                "is_primary": False,
            },
        ],
        "signals": [
            (SignalType.ADVERTISING, "Campanha no Meta Ads focada em carga imediata de implantes."),
            (SignalType.WEBSITE_QUALITY, "Website com scanner 3D e tour virtual 360º da clínica."),
            (SignalType.MULTI_LOCATION, "2 clínicas operacionais na zona metropolitana do Porto."),
            (SignalType.HIGH_TICKET, "Especializada exclusivamente em implantologia avançada e cirurgia ortognática."),
        ],
        "enrichment": {
            "growth_probability": 86,
            "technology_maturity": 90,
            "marketing_sophistication": 82,
            "expansion_probability": 78,
            "explanation": (
                "Forte alinhamento tecnológico e foco em reabilitação oral de alta complexidade. "
                "Boa maturidade digital e potencial elevado para aquisição de equipamentos de diagnóstico digital."
            ),
        },
    },
    {
        "name": "Sorrisos de Braga - Odontologia Integrada",
        "place_id": "demo_place_03",
        "phone": "+351 253 204 560",
        "website": "https://sorrisosbraga.pt",
        "google_rating": 4.7,
        "google_review_count": 189,
        "locations_count": 1,
        "social_urls": ["https://instagram.com/sorrisosdebraga"],
        "locations": [
            {
                "street": "Avenida da Liberdade 65",
                "city": "Braga",
                "state": "Braga",
                "postal_code": "4710-251",
                "country": "Portugal",
                "lat": 41.5503,
                "lng": -8.4201,
                "is_primary": True,
            },
        ],
        "signals": [
            (SignalType.HIRING, "Procura assistente dentária e rececionista para expansão de horário."),
            (SignalType.ADVERTISING, "Google Search Ads para 'dentista braga centro'."),
            (SignalType.WEBSITE_QUALITY, "Página rápida com agendamento via WhatsApp integrado."),
            (SignalType.HIGH_TICKET, "Serviços de ortodontia invisível e clareamento a laser."),
        ],
        "enrichment": {
            "growth_probability": 75,
            "technology_maturity": 68,
            "marketing_sophistication": 70,
            "expansion_probability": 65,
            "explanation": (
                "Clínica em fase de consolidação regional com investimento em marketing local e contratação de suporte. "
                "Boa oportunidade para ferramentas de fidelização e automação de agendamentos."
            ),
        },
    },
    {
        "name": "Centro Dentário do Parque das Nações",
        "place_id": "demo_place_04",
        "phone": "+351 21 895 4400",
        "website": "https://dentariaparque.pt",
        "google_rating": 4.9,
        "google_review_count": 520,
        "locations_count": 2,
        "social_urls": ["https://instagram.com/dentariaparque", "https://linkedin.com/company/dentariaparque"],
        "locations": [
            {
                "street": "Alameda dos Oceanos 41R",
                "city": "Lisboa",
                "state": "Lisboa",
                "postal_code": "1990-203",
                "country": "Portugal",
                "lat": 38.7672,
                "lng": -9.0965,
                "is_primary": True,
            },
            {
                "street": "Avenida Dom João II 35",
                "city": "Lisboa",
                "state": "Lisboa",
                "postal_code": "1990-097",
                "country": "Portugal",
                "lat": 38.7710,
                "lng": -9.0980,
                "is_primary": False,
            },
        ],
        "signals": [
            (SignalType.HIRING, "Contratação aberta para gestor de clínica e dentista ortodontista."),
            (SignalType.ADVERTISING, "Anúncios Meta Ads direcionados a executivos do Parque das Nações."),
            (SignalType.WEBSITE_QUALITY, "Portal do paciente com visualização de exames e radiografias."),
            (SignalType.MULTI_LOCATION, "Duas clínicas ativas na zona oriental de Lisboa."),
            (SignalType.HIGH_TICKET, "Laboratório de prótese digital CAD/CAM próprio na unidade."),
        ],
        "enrichment": {
            "growth_probability": 96,
            "technology_maturity": 95,
            "marketing_sophistication": 90,
            "expansion_probability": 92,
            "explanation": (
                "Perfil empresarial altamente estruturado, público corporativo de alto rendimento e tecnologia de ponta. "
                "Score máximo de propensão de compra para inovação em saúde oral."
            ),
        },
    },
    {
        "name": "Clínica Odontológica Dra. Sofia Martins",
        "place_id": "demo_place_05",
        "phone": "+351 239 824 110",
        "website": "https://drasofiamartins.pt",
        "google_rating": 4.6,
        "google_review_count": 92,
        "locations_count": 1,
        "social_urls": [],
        "locations": [
            {
                "street": "Rua de Tomar 18",
                "city": "Coimbra",
                "state": "Coimbra",
                "postal_code": "3000-401",
                "country": "Portugal",
                "lat": 40.2110,
                "lng": -8.4292,
                "is_primary": True,
            },
        ],
        "signals": [
            (SignalType.WEBSITE_QUALITY, "Website institucional com lista de serviços e equipa clínica."),
            (SignalType.HIGH_TICKET, "Odontopediatria e ortodontia preventiva."),
        ],
        "enrichment": {
            "growth_probability": 52,
            "technology_maturity": 48,
            "marketing_sophistication": 40,
            "expansion_probability": 35,
            "explanation": (
                "Consultório tradicional com clientela de bairro estável e pouca tração de marketing digital. "
                "Prioridade moderada para abordagem comercial."
            ),
        },
    },
    {
        "name": "Dental Care Algarve - Faro & Portimão",
        "place_id": "demo_place_06",
        "phone": "+351 289 800 220",
        "website": "https://dentalcarealgarve.com",
        "google_rating": 4.8,
        "google_review_count": 274,
        "locations_count": 2,
        "social_urls": ["https://instagram.com/dentalcarealgarve"],
        "locations": [
            {
                "street": "Rua de Santo António 44",
                "city": "Faro",
                "state": "Faro",
                "postal_code": "8000-283",
                "country": "Portugal",
                "lat": 37.0163,
                "lng": -7.9351,
                "is_primary": True,
            },
            {
                "street": "Avenida 28 de Maio 12",
                "city": "Portimão",
                "state": "Faro",
                "postal_code": "8500-501",
                "country": "Portugal",
                "lat": 37.1360,
                "lng": -8.5375,
                "is_primary": False,
            },
        ],
        "signals": [
            (SignalType.ADVERTISING, "Campanhas multilingues (EN/PT/FR) para turismo dentário e expat community."),
            (SignalType.WEBSITE_QUALITY, "Website multilingue responsivo com chat ao vivo."),
            (SignalType.MULTI_LOCATION, "Unidades em Faro e Portimão."),
            (SignalType.HIGH_TICKET, "Tratamentos estéticos de alta rentabilidade (veneers e reabilitação oral)."),
        ],
        "enrichment": {
            "growth_probability": 88,
            "technology_maturity": 79,
            "marketing_sophistication": 89,
            "expansion_probability": 80,
            "explanation": (
                "Forte orientação comercial internacional e captação de clientes estrangeiros com alto poder de compra. "
                "Excelente perfil para fornecedores B2B de valor agregado."
            ),
        },
    },
    {
        "name": "Consultório Dentário Dr. Manuel Ferreira",
        "place_id": "demo_place_07",
        "phone": "+351 256 600 120",
        "website": None,
        "google_rating": 4.1,
        "google_review_count": 22,
        "locations_count": 1,
        "social_urls": [],
        "locations": [
            {
                "street": "Praça da República 10",
                "city": "Santa Maria da Feira",
                "state": "Aveiro",
                "postal_code": "4520-160",
                "country": "Portugal",
                "lat": 40.9258,
                "lng": -8.5422,
                "is_primary": True,
            },
        ],
        "signals": [],
        "enrichment": {
            "growth_probability": 20,
            "technology_maturity": 22,
            "marketing_sophistication": 15,
            "expansion_probability": 10,
            "explanation": (
                "Sem website ou canais digitais detetados. Prática individual tradicional sem sinais imediatos de expansão."
            ),
        },
    },
    {
        "name": "Clínica São Jerónimo - Almada Dental",
        "place_id": "demo_place_08",
        "phone": "+351 21 274 9911",
        "website": "https://saojeronimodental.pt",
        "google_rating": 4.5,
        "google_review_count": 140,
        "locations_count": 1,
        "social_urls": ["https://facebook.com/saojeronimodental"],
        "locations": [
            {
                "street": "Avenida Dom Nuno Álvares Pereira 50",
                "city": "Almada",
                "state": "Setúbal",
                "postal_code": "2800-176",
                "country": "Portugal",
                "lat": 38.6791,
                "lng": -9.1570,
                "is_primary": True,
            },
        ],
        "signals": [
            (SignalType.HIRING, "Vaga para higienista oral a tempo inteiro."),
            (SignalType.WEBSITE_QUALITY, "Site com formulário simples de contacto."),
        ],
        "enrichment": {
            "growth_probability": 60,
            "technology_maturity": 55,
            "marketing_sophistication": 48,
            "expansion_probability": 42,
            "explanation": (
                "Clínica sólida na Margem Sul com crescimento orgânico de pacientes e contratação de equipa de apoio."
            ),
        },
    },
    {
        "name": "Artis Dental Studio - Cascais",
        "place_id": "demo_place_09",
        "phone": "+351 21 486 3311",
        "website": "https://artisdentalstudio.com",
        "google_rating": 5.0,
        "google_review_count": 160,
        "locations_count": 1,
        "social_urls": ["https://instagram.com/artisdentalcascais"],
        "locations": [
            {
                "street": "Rua Frederico Arouca 78",
                "city": "Cascais",
                "state": "Lisboa",
                "postal_code": "2750-355",
                "country": "Portugal",
                "lat": 38.6975,
                "lng": -9.4201,
                "is_primary": True,
            },
        ],
        "signals": [
            (SignalType.ADVERTISING, "Instagram Ads focado em harmonização orofacial e design de sorriso."),
            (SignalType.WEBSITE_QUALITY, "Design minimalista premium e fotografia profissional da equipa."),
            (SignalType.HIGH_TICKET, "Lentes de contacto dentárias e reabilitação estética exclusiva."),
        ],
        "enrichment": {
            "growth_probability": 82,
            "technology_maturity": 85,
            "marketing_sophistication": 88,
            "expansion_probability": 68,
            "explanation": (
                "Boutique clinic estética de posicionamento ultra-premium com avaliação 5.0 estrelas. "
                "Excelente apetite para tecnologia e produtos de prestígio."
            ),
        },
    },
    {
        "name": "Clínica OdontoGuimarães",
        "place_id": "demo_place_10",
        "phone": "+351 253 515 880",
        "website": "https://odontoguimaraes.pt",
        "google_rating": 4.4,
        "google_review_count": 87,
        "locations_count": 1,
        "social_urls": [],
        "locations": [
            {
                "street": "Alameda de São Dâmaso 22",
                "city": "Guimarães",
                "state": "Braga",
                "postal_code": "4810-286",
                "country": "Portugal",
                "lat": 41.4425,
                "lng": -8.2933,
                "is_primary": True,
            },
        ],
        "signals": [
            (SignalType.WEBSITE_QUALITY, "Website com catálogo de tratamentos gerais."),
        ],
        "enrichment": {
            "growth_probability": 45,
            "technology_maturity": 40,
            "marketing_sophistication": 35,
            "expansion_probability": 30,
            "explanation": (
                "Prática clínica local com foco em clínica geral e conservadora."
            ),
        },
    },
]


def seed_database():
    session = SessionLocal()
    try:
        # Check active scoring config
        scoring_config_model = (
            session.query(ScoringConfigModel).filter_by(active=True).first()
        )
        if not scoring_config_model:
            print("No active scoring config found! Ensure alembic migrations ran.", file=sys.stderr)
            return 1

        from app.domain.entities.scoring_config import ScoreBand
        bands = [
            ScoreBand(name=b["name"], min=b["min"], max=b["max"])
            for b in scoring_config_model.bands
        ]
        scoring_config = ScoringConfig(
            version=scoring_config_model.version,
            active=scoring_config_model.active,
            weights=scoring_config_model.weights,
            bands=bands,
        )

        scoring_service = ScoringService()
        now = datetime.now(UTC)

        print(f"Seeding database with {len(SAMPLE_CLINICS)} demo clinics...")

        for idx, item in enumerate(SAMPLE_CLINICS, 1):
            existing_clinic = (
                session.query(ClinicModel).filter_by(place_id=item["place_id"]).first()
            )
            if existing_clinic:
                session.delete(existing_clinic)
                session.flush()

            clinic_id = uuid4()
            clinic = ClinicModel(
                id=clinic_id,
                place_id=item["place_id"],
                name=item["name"],
                phone=item["phone"],
                website=item["website"],
                google_rating=item["google_rating"],
                google_review_count=item["google_review_count"],
                locations_count=item["locations_count"],
                social_urls=item["social_urls"],
                created_at=now - timedelta(days=idx * 2),
                updated_at=now - timedelta(hours=idx),
            )
            session.add(clinic)
            session.flush()

            # Add locations
            for loc_data in item["locations"]:
                loc = LocationModel(
                    id=uuid4(),
                    clinic_id=clinic_id,
                    street=loc_data["street"],
                    city=loc_data["city"],
                    state=loc_data["state"],
                    postal_code=loc_data["postal_code"],
                    country=loc_data["country"],
                    lat=loc_data["lat"],
                    lng=loc_data["lng"],
                    is_primary=loc_data["is_primary"],
                )
                session.add(loc)

            # Add signals
            domain_signals = []
            for sig_type, evidence in item["signals"]:
                sig_id = uuid4()
                weight = scoring_config.weights.get(sig_type.value, 0)
                sig_model = SignalModel(
                    id=sig_id,
                    clinic_id=clinic_id,
                    type=sig_type.value,
                    applied_weight=weight,
                    evidence=evidence,
                    confidence=0.95,
                    detected_at=now - timedelta(days=1, hours=idx),
                )
                session.add(sig_model)

                domain_signals.append(
                    Signal(
                        id=sig_id,
                        clinic_id=clinic_id,
                        type=sig_type,
                        applied_weight=weight,
                        evidence=evidence,
                        confidence=0.95,
                        detected_at=now - timedelta(days=1, hours=idx),
                    )
                )

            session.flush()

            # Compute score using standard domain logic
            computed_score = scoring_service.compute(domain_signals, scoring_config)
            score_model = ScoreModel(
                id=uuid4(),
                clinic_id=clinic_id,
                total=computed_score.total,
                breakdown=computed_score.breakdown.to_dict(),
                priority=computed_score.priority.value,
                config_version=scoring_config.version,
                computed_at=now - timedelta(hours=idx),
            )
            session.add(score_model)

            # Add AI enrichment
            enrich_data = item["enrichment"]
            enrichment_model = EnrichmentModel(
                id=uuid4(),
                clinic_id=clinic_id,
                growth_probability=enrich_data["growth_probability"],
                technology_maturity=enrich_data["technology_maturity"],
                marketing_sophistication=enrich_data["marketing_sophistication"],
                expansion_probability=enrich_data["expansion_probability"],
                explanation=enrich_data["explanation"],
                provider="demo_gpt",
                model="gpt-4o-mini",
                prompt_version="clinic_enrichment_v1",
                created_at=now - timedelta(hours=idx),
            )
            session.add(enrichment_model)

            session.commit()
            print(
                f"  [{idx}/{len(SAMPLE_CLINICS)}] {clinic.name} -> "
                f"Score: {computed_score.total} ({computed_score.priority.value}), "
                f"Signals: {len(domain_signals)}, Locations: {len(item['locations'])}"
            )

        print("\nDatabase seeded successfully!")
        return 0
    except Exception as exc:
        session.rollback()
        print(f"Error seeding database: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(seed_database())
