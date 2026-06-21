# DataInsight Sports Analytics

MVP completo para scout esportivo: times, atletas, jogos, eventos, análise de adversários, plano de jogo e dashboard.

## Rodar local

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Abra `frontend/index.html` no navegador.

Por padrão usa SQLite local. Para Supabase/Render, configure variáveis:

- `DB_URL=postgresql://usuario:senha@host:5432/postgres`
- `JWT_SECRET=uma-chave-segura`

No frontend, se publicar no Netlify, ajuste a URL da API no console do navegador:

```js
localStorage.setItem('API_URL','https://seu-backend.onrender.com')
```

Depois recarregue a página.

## Próximos módulos recomendados

- PDF do plano de jogo
- Upload de vídeo e marcação por minuto
- Heatmap por zona do campo
- Ranking de atletas por função
- Permissões admin/gestor/clube
