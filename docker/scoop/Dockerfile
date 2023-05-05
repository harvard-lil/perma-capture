FROM node:18.16-bullseye

ENV NODE_ENV=development

RUN mkdir -p /scoop
WORKDIR /scoop

RUN npm init -y && npm install @harvard-lil/scoop@0.2.7
RUN npx playwright install-deps chromium

CMD echo "Ready to scoop!"
