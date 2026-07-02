FROM node:22-alpine

WORKDIR /app

# Deliberately not copying package-lock.json: it's resolved on the dev's host
# (often darwin-arm64), and npm has a long-standing bug (npm/cli#4828) where a
# lockfile from one platform skips the optional platform-specific binary of the
# current platform — e.g. @rollup/rollup-linux-x64-musl on Alpine. Letting npm
# re-resolve on the target arch avoids the "Cannot find module …" crash.
COPY package.json ./
RUN npm install --no-audit --no-fund

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
