/* eslint-disable @typescript-eslint/no-var-requires */
const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

const isProduction = process.env.NODE_ENV === "production";

module.exports = {
    entry: {
        taskpane: "./src/taskpane.ts",
        commands: "./src/commands.ts",
    },
    output: {
        filename: "[name].js",
        path: path.resolve(__dirname, "dist"),
        clean: true,
    },
    resolve: {
        extensions: [".ts", ".js"],
    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                use: "ts-loader",
                exclude: /node_modules/,
            },
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"],
            },
        ],
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: "./src/taskpane.html",
            filename: "taskpane.html",
            chunks: ["taskpane"],
        }),
        new HtmlWebpackPlugin({
            template: "./src/commands.html",
            filename: "commands.html",
            chunks: ["commands"],
        }),
        new CopyWebpackPlugin({
            patterns: [
                {
                    from: "assets",
                    to: "assets",
                    noErrorOnMissing: true,
                },
            ],
        }),
    ],
    devServer: {
        static: path.resolve(__dirname, "dist"),
        port: 3000,
        https: true, // Office add-ins require HTTPS
        headers: {
            "Access-Control-Allow-Origin": "*",
        },
    },
    devtool: isProduction ? "source-map" : "eval-source-map",
};
