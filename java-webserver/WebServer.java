import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class WebServer {
    private static final Map<String, String> MIME_TYPES = new HashMap<>();
    private static List<String> messages = new ArrayList<>();
    
    static {
        MIME_TYPES.put("html", "text/html");
        MIME_TYPES.put("css", "text/css");
        MIME_TYPES.put("js", "application/javascript");
        MIME_TYPES.put("png", "image/png");
        MIME_TYPES.put("jpg", "image/jpeg");
    }
    
    public static void main(String[] args) throws IOException {
        int port = 8080;
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        
        // Статические файлы
        server.createContext("/", exchange -> handleRequest(exchange, "page1.html"));
        server.createContext("/projects", exchange -> handleRequest(exchange, "page2.html"));
        server.createContext("/contact", exchange -> handleRequest(exchange, "page3.html"));
        server.createContext("/style.css", exchange -> serveStatic(exchange, "style.css"));
        server.createContext("/script.js", exchange -> serveStatic(exchange, "script.js"));
        
        // API для формы
        server.createContext("/api/send-message", exchange -> {
            if ("POST".equals(exchange.getRequestMethod())) {
                handleMessageForm(exchange);
            }
        });
        
        // API для получения сообщений
        server.createContext("/api/messages", exchange -> {
            if ("GET".equals(exchange.getRequestMethod())) {
                String json = "{\"messages\":" + messages.size() + "}";
                sendResponse(exchange, json, "application/json");
            }
        });
        
        server.setExecutor(null);
        server.start();
        
        System.out.println("✨ Сервер запущен: http://localhost:" + port);
        System.out.println("📊 API:");
        System.out.println("  GET  /                 - Главная страница");
        System.out.println("  POST /api/send-message - Отправить сообщение");
        System.out.println("  GET  /api/messages     - Статистика сообщений");
    }
    
    private static void handleRequest(HttpExchange exchange, String fileName) throws IOException {
        try {
            String content = new String(Files.readAllBytes(Paths.get(fileName)));
            sendResponse(exchange, content, "text/html");
        } catch (IOException e) {
            sendError(exchange, 404, "Файл не найден");
        }
    }
    
    private static void serveStatic(HttpExchange exchange, String fileName) throws IOException {
        try {
            String ext = fileName.substring(fileName.lastIndexOf(".") + 1);
            String mimeType = MIME_TYPES.getOrDefault(ext, "text/plain");
            String content = new String(Files.readAllBytes(Paths.get(fileName)));
            sendResponse(exchange, content, mimeType);
        } catch (IOException e) {
            sendError(exchange, 404, "Файл не найден");
        }
    }
    
    private static void handleMessageForm(HttpExchange exchange) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(exchange.getRequestBody()))) {
            StringBuilder body = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                body.append(line);
            }
            
            // Простая обработка формы
            messages.add(body.toString());
            
            String response = "{\"success\":true,\"message\":\"Сообщение сохранено! Всего сообщений: " + messages.size() + "\"}";
            sendResponse(exchange, response, "application/json");
        }
    }
    
    private static void sendResponse(HttpExchange exchange, String content, String contentType) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", contentType + "; charset=UTF-8");
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(200, content.getBytes().length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(content.getBytes());
        }
    }
    
    private static void sendError(HttpExchange exchange, int code, String message) throws IOException {
        String error = "<html><body><h1>Ошибка " + code + "</h1><p>" + message + "</p></body></html>";
        exchange.sendResponseHeaders(code, error.getBytes().length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(error.getBytes());
        }
    }
}