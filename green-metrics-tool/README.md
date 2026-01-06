This measures the nextcloud calendar app with the Green Metrics Tool

## Memory problem

Webpack needs a lot of memory on install. If you have limited memory on your system you will need to add this at the bottom of your webpack.config.js

```
const TerserPlugin = require('terser-webpack-plugin')
const isProd =
	process.env.NODE_ENV === 'production'
	|| process.env.WEBPACK_NODE_ENV === 'production'
	|| webpackConfig.mode === 'production'

if (isProd) {
	webpackConfig.optimization = webpackConfig.optimization || {}

	const minimizers = webpackConfig.optimization.minimizer || []

	// Keep non-Terser minimizers (e.g., CSS minimizer), replace Terser with a constrained instance
	webpackConfig.optimization.minimizer = [
		...minimizers.filter(m => m?.constructor?.name !== 'TerserPlugin'),
		new TerserPlugin({
			parallel: 1,      // strongest lever for peak RSS
			// If you still OOM, change to: parallel: false
		}),
	]
}
```