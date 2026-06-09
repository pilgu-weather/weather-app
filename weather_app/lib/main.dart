import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: WeatherFitWebView(),
    );
  }
}

class WeatherFitWebView extends StatefulWidget {
  const WeatherFitWebView({super.key});

  @override
  State<WeatherFitWebView> createState() => _WeatherFitWebViewState();
}

class _WeatherFitWebViewState extends State<WeatherFitWebView> {
  late final WebViewController controller;

  @override
  void initState() {
    super.initState();

    controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(
        Uri.parse("https://weather-app-1-xy3b.onrender.com"),
      );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Weather Fit"),
      ),
      body: WebViewWidget(
        controller: controller,
      ),
    );
  }
}