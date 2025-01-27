module.exports = {
    proxy: "https://circusfactions.local",
    files: ["public/**/*.html", "public/**/*.css", "public/**/*.js"],
    notify: false,
    https: {
        key: "/Users/phillip/GitHub/mac-admin/docker/caddy/local-certs/localhost+3-key.pem",
        cert: "/Users/phillip/GitHub/mac-admin/docker/caddy/local-certs/localhost+3.pem"
    }
};