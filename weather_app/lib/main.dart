import 'dart:io';

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';

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
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (NavigationRequest request) async {
            debugPrint("[WeatherFit] navigation request: ${request.url}");

            final uri = Uri.parse(request.url);

            if (request.url.contains("/download-outfit-image")) {
              debugPrint("[WeatherFit] download url detected");

              try {
                final result = await launchUrl(
                  uri,
                  mode: LaunchMode.externalApplication,
                );

                debugPrint("[WeatherFit] launchUrl result: $result");
              } catch (error, stackTrace) {
                debugPrint("[WeatherFit] launchUrl error: $error");
                debugPrint("[WeatherFit] launchUrl stack: $stackTrace");
              }

              return NavigationDecision.prevent;
            }

            return NavigationDecision.navigate;
          },
        ),
      );

    _configureWebView();
  }

  Future<void> _configureWebView() async {
    if (Platform.isAndroid &&
        controller.platform is AndroidWebViewController) {
      final androidController =
          controller.platform as AndroidWebViewController;

      await androidController.setGeolocationEnabled(true);

      await androidController.setGeolocationPermissionsPromptCallbacks(
        onShowPrompt: (GeolocationPermissionsRequestParams request) async {
          final status =
              await Permission.locationWhenInUse.request();

          return GeolocationPermissionsResponse(
            allow: status.isGranted,
            retain: true,
          );
        },
      );
    }

    await controller.loadRequest(
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
