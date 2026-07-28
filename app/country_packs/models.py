from pydantic import BaseModel, Field, field_validator


class Language(BaseModel):
    code: str = Field(..., min_length=2, max_length=8)
    name: str = Field(..., min_length=1)
    primary: bool = False


class LanguagesFile(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    status: str = "pending_population"
    languages: list[Language] = Field(default_factory=list)

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError(f"country_code moet hoofdletters zijn: {v}")
        return v

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: list[Language]) -> list[Language]:
        if not v:
            return v
        codes = [lang.code for lang in v]
        if len(codes) != len(set(codes)):
            raise ValueError("Dubbele taalcodes niet toegestaan")
        primary_count = sum(1 for lang in v if lang.primary)
        if primary_count != 1:
            raise ValueError(f"Precies één primaire taal vereist, gevonden: {primary_count}")
        return v


class LeakTerm(BaseModel):
    term: str = Field(..., min_length=1)


class ContextTermsFile(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    status: str = "pending_population"
    context_terms: list[LeakTerm] = Field(default_factory=list)

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError(f"country_code moet hoofdletters zijn: {v}")
        return v

    @field_validator("context_terms")
    @classmethod
    def dedup(cls, v: list[LeakTerm]) -> list[LeakTerm]:
        seen: set[str] = set()
        result: list[LeakTerm] = []
        for t in v:
            key = t.term.lower()
            if key not in seen:
                seen.add(key)
                result.append(t)
        return result


class LeakAssertionTermsFile(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    status: str = "pending_population"
    leak_assertion_terms: list[LeakTerm] = Field(default_factory=list)

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError(f"country_code moet hoofdletters zijn: {v}")
        return v

    @field_validator("leak_assertion_terms")
    @classmethod
    def dedup(cls, v: list[LeakTerm]) -> list[LeakTerm]:
        seen: set[str] = set()
        result: list[LeakTerm] = []
        for t in v:
            key = t.term.lower()
            if key not in seen:
                seen.add(key)
                result.append(t)
        return result


class Entity(BaseModel):
    canonical_name: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    aliases: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)


class EntitiesFile(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    status: str = "pending_population"
    entities: list[Entity] = Field(default_factory=list)

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError(f"country_code moet hoofdletters zijn: {v}")
        return v

    @field_validator("entities")
    @classmethod
    def dedup_entities(cls, v: list[Entity]) -> list[Entity]:
        names = [e.canonical_name.lower() for e in v]
        if len(names) != len(set(names)):
            raise ValueError("Dubbele entiteiten op canonical_name niet toegestaan")
        return v


class SourceDef(BaseModel):
    id: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1)
    type: str = Field(...)
    source_role: str = Field(default="signal")
    source_category: str = Field(default="specialist_blog")
    discovery_priority: str = Field(default="secondary")
    can_create_primary_claim: bool = True
    base_url: str = Field(...)
    poll_url: str = Field(...)
    languages: list[str] = Field(default_factory=list)
    content_modes: list[str] = Field(default_factory=list)
    access_method: str = Field(default="")
    connector_config: dict = Field(default_factory=dict)
    validation_notes: str | None = None
    validated_at: str | None = None
    access_restrictions: str | None = None
    expected_content_types: list[str] = Field(default_factory=list)
    enabled: bool = True
    poll_interval_minutes: int = Field(default=30, ge=5)

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        allowed = {"rss", "html", "archive", "git_host", "web_archive", "public_channel"}
        if v not in allowed:
            raise ValueError(f"Type moet een van {allowed} zijn, niet: {v}")
        return v

    @field_validator("source_role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        allowed = {"origin_candidate", "distribution", "archive", "mirror", "signal", "confirmation", "official_response"}
        if v not in allowed:
            raise ValueError(f"source_role moet een van {allowed} zijn, niet: {v}")
        return v

    @field_validator("source_category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        allowed = {"leak_archive", "document_archive", "dataset_index", "git_host", "file_host", "torrent_index", "ipfs_index", "public_channel", "paste_site", "web_archive", "whistleblower_platform", "specialist_blog", "mainstream_media", "government", "parliament", "raw_leak_archive", "user_upload_archive", "open_directory", "independent_researcher", "mirror_index", "repository_search"}
        if v not in allowed:
            raise ValueError(f"source_category moet een van {allowed} zijn, niet: {v}")
        return v

    @field_validator("discovery_priority")
    @classmethod
    def valid_priority(cls, v: str) -> str:
        if v not in ("primary", "secondary", "low"):
            raise ValueError(f"discovery_priority moet primary/secondary/low zijn, niet: {v}")
        return v

    @field_validator("base_url", "poll_url")
    @classmethod
    def valid_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL moet beginnen met http:// of https://: {v}")
        return v


class SourcesFile(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    status: str = "pending_population"
    sources: list[SourceDef] = Field(default_factory=list)

    @field_validator("country_code")
    @classmethod
    def upper_country(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError(f"country_code moet hoofdletters zijn: {v}")
        return v


class CountryPack(BaseModel):
    country_code: str
    status: str = "pending_population"
    languages: LanguagesFile | None = None
    context_terms: ContextTermsFile | None = None
    leak_assertion_terms: LeakAssertionTermsFile | None = None
    entities: EntitiesFile | None = None
    sources: SourcesFile | None = None
    errors: list[str] = Field(default_factory=list)


class CountryPackValidationError(BaseModel):
    file: str
    errors: list[str]


class CountryPackValidationResult(BaseModel):
    total_packs: int = 0
    valid_packs: int = 0
    invalid_packs: int = 0
    errors: list[CountryPackValidationError] = Field(default_factory=list)
    duplicate_source_ids: list[str] = Field(default_factory=list)
