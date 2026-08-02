---
name: fastapi
description: Best practice e convenzioni per costruire API con FastAPI - struttura progetto, async/await, dependency injection, validazione Pydantic, SQLModel/SQLAlchemy async, autenticazione JWT, gestione errori, testing. Usa quando scrivi, revisioni o modifichi codice FastAPI, endpoint, modelli, o servizi.
---

# FastAPI Conventions

## Struttura del progetto

Organizza per dominio/feature, non per tipo di file. Ogni modulo di dominio contiene i propri model, schema, service e router:

```
src/
├── User/
│   ├── model.py       # SQLModel/ORM
│   ├── schema.py      # Pydantic DTO (request/response)
│   ├── service.py      # business logic
│   └── router.py       # endpoint FastAPI
├── Auth/
│   ├── model.py
│   ├── schema.py
│   ├── service.py
│   ├── utils.py         # helper (token, hashing)
│   └── router.py
config/
├── database.py          # engine, sessionmaker, SessionDep
└── settings.py          # Pydantic Settings, env vars
main.py
```

Evita un unico `models.py`/`routes.py` monolitico oltre poche decine di righe: non scala e crea merge conflict continui.

## Dependency Injection

Usa sempre `Annotated` + `Depends` per le dipendenze condivise (sessione DB, utente corrente, paginazione):

```python
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/me")
async def read_me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
```

Non istanziare sessioni o servizi manualmente dentro l'endpoint: se non passa da `Depends`, non è testabile né sovrascrivibile in test.

## Async, sempre coerente

- Se usi un ORM async (SQLModel/SQLAlchemy async, Tortoise), **ogni funzione che tocca il DB è `async def`** e usa `await`.
- Non chiamare mai codice sincrono e bloccante (bcrypt, hashing pesante, chiamate HTTP sincrone, lettura file grandi) direttamente dentro una funzione `async def`: blocchi l'event loop e rallenti *tutte* le richieste concorrenti.

```python
import asyncio
hashed = await asyncio.to_thread(bcrypt.hashpw, password_bytes, salt)
```

- Se una funzione non fa I/O e non chiama nulla di async, tienila sincrona: non serve `async def` ovunque per moda.

## Validazione con Pydantic

- Ogni request/response passa da uno schema Pydantic esplicito (`schema.py`), mai da un dict grezzo o dal model ORM diretto in output (rischio di esporre campi sensibili come password hash).
- Usa `model_config = ConfigDict(from_attributes=True)` per convertire da ORM a schema Pydantic v2.
- Valida vincoli di dominio nello schema quando possibile (`EmailStr`, `Field(min_length=...)`, `field_validator`), non solo nel service.

```python
from pydantic import BaseModel, EmailStr, Field

class RegisterUserDto(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8)
```

## Gestione errori

- Usa `HTTPException` con `status.HTTP_xxx` (mai codici numerici hardcoded) e `detail` chiaro ma senza rivelare dettagli interni (stacktrace, query SQL, nomi di colonne).
- Per errori di dominio ricorrenti, considera eccezioni custom catturate da un `exception_handler` centralizzato in `main.py`, invece di ripetere `try/except` in ogni service.
- Non esporre mai messaggi diversi per "utente non trovato" vs "password errata" su endpoint di login: usa un messaggio generico ("Invalid email or password") per evitare enumerazione account. Fa eccezione la registrazione, dove di solito si accetta il trade-off UX (es. 409 "Email already in use").

## Sicurezza — autenticazione

- **Password**: bcrypt (o argon2id via `argon2-cffi`, preferibile per progetti nuovi) — mai MD5/SHA diretti senza salt. Esegui sempre via `asyncio.to_thread`.
- **Timing attack su login**: esegui sempre il confronto password (anche con un hash "dummy" precalcolato) quando l'utente non esiste, per non rivelare via timing se un'email è registrata.
- **JWT access token**: vita breve (10–15 minuti), payload minimale (`sub`, `iat`, `exp`) — evita di includere dati mutabili come email/username che possono disallinearsi dal DB.
- **Refresh token**: generato con `secrets.token_urlsafe(64)` (alta entropia, no bcrypt necessario), salvato nel DB **solo come hash** (SHA-256 va bene), mai in chiaro. Il valore raw va restituito al client una sola volta, mai più recuperabile.
- **Scadenza refresh token**: campo `expiration` esplicito nel modello, controllato ad ogni refresh — un token senza scadenza è valido per sempre se rubato.
- **Rotazione one-time-use**: ad ogni refresh, elimina il vecchio token e generane uno nuovo. Se un token già consumato viene ripresentato, è indizio di furto: valuta la revoca di tutte le sessioni dell'utente.
- Usa sempre `datetime.now(timezone.utc)`, mai `datetime.utcnow()` (deprecato da Python 3.12) — occhio a normalizzare i datetime "naive" letti da DB che non salvano il timezone (es. SQLite).

## Configurazione

- Centralizza tutte le variabili d'ambiente in `config/settings.py` con Pydantic `BaseSettings`, mai `os.environ.get(...)` sparso nel codice.
- Non committare segreti: `SECRET_KEY_JWT` e simili solo da `.env`/secret manager, mai hardcoded né in default di fallback.

## Testing

- Usa `httpx.AsyncClient` con `ASGITransport` per testare gli endpoint async end-to-end.
- Sovrascrivi le dipendenze (`app.dependency_overrides`) per iniettare una sessione DB di test (SQLite in-memory o DB di test dedicato), mai puntare al DB di produzione/sviluppo nei test.
- Testa esplicitamente i casi limite di auth: token scaduto, token già usato (rotazione), utente inesistente, password errata — non solo il happy path.

## Performance

- Paginazione esplicita su ogni endpoint che lista risorse (`limit`/`offset` o cursor-based), mai `SELECT *` senza limite.
- Usa `selectinload`/`joinedload` espliciti per le relazioni che sai di dover caricare, per evitare N+1 query silenziose.
- Rate limiting su endpoint sensibili (login, register, refresh, reset password) a livello di middleware o reverse proxy.