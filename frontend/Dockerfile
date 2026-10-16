# stage one builds the react app with node
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
# install the exact package versions from the lock file
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# stage two serves the built files with an nginx image that does not run as root
# it uses user 101 and port 8080
FROM nginxinc/nginx-unprivileged:1.29-alpine
# switch to root for a moment to install security updates
USER root
RUN apk upgrade --no-cache
# copy only the built website from stage one and our nginx settings
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# go back to the normal user
USER 101
EXPOSE 8080
