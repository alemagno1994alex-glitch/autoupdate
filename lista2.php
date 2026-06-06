<?php
/**
 * PepperStream Proxy - Genera M3U con formato KODIPROP
 * Output: #EXTINF + #KODIPROP + URL pulito
 */

class PepperProxy {
    private const PEPPER_BASE = 'https://pepperstream.xyz/TV';
    private const PEPPER_PASS = 'CHILI_98676998_84';
    private const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0';
    
    private const CORS_HEADERS = [
        'Access-Control-Allow-Origin' => '*',
        'Access-Control-Allow-Methods' => 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers' => '*'
    ];

    // File per salvare la sessione
    private const SESSION_FILE = 'pepper_session.json';
    private const SESSION_TTL = 3600;

    // MAPPATURA NOMI CANALI -> GRUPPI
    private const CHANNEL_TO_GROUP = [
        // CINEMA
        "Sky Cinema Uno" => "CINEMA",
        "Cinema Uno" => "CINEMA",
        "Sky Cinema Due" => "CINEMA",
        "Cinema Due" => "CINEMA",
        "Sky Cinema Collection" => "CINEMA",
        "Cinema Collection" => "CINEMA",
        "Sky Cinema Family" => "CINEMA",
        "Cinema Family" => "CINEMA",
        "Sky Cinema Illumination" => "CINEMA",
        "Sky Cinema Action" => "CINEMA",
        "Cinema Action" => "CINEMA",
        "Sky Cinema Suspense" => "CINEMA",
        "Cinema Suspense" => "CINEMA",
        "Sky Cinema Romance" => "CINEMA",
        "Cinema Romance" => "CINEMA",
        "Sky Cinema Drama" => "CINEMA",
        "Cinema Drama" => "CINEMA",
        "Sky Cinema Comedy" => "CINEMA",
        "Cinema Comedy" => "CINEMA",
        "Sky Cinema Stories" => "CINEMA",
        "Cinema Stories" => "CINEMA",
        
        // INTRATTENIMENTO
        "Sky Uno" => "INTRATTENIMENTO",
        "Sky Uno +" => "INTRATTENIMENTO",
        "Sky Atlantic" => "INTRATTENIMENTO",
        "Sky Serie" => "INTRATTENIMENTO",
        "Sky Investigation" => "INTRATTENIMENTO",
        "Sky Collection" => "INTRATTENIMENTO",
        "Comedy Central" => "INTRATTENIMENTO",
        "Mtv" => "INTRATTENIMENTO",
        "Sky Tg24" => "INTRATTENIMENTO",
        "Sky Arte" => "INTRATTENIMENTO",
        "Sky Documentaries" => "INTRATTENIMENTO",
        "Sky Nature" => "INTRATTENIMENTO",
        "Sky Adventure" => "INTRATTENIMENTO",
        "History" => "INTRATTENIMENTO",
        "Sky Crime" => "INTRATTENIMENTO",
        
        // SPORT
        "Sky Sport 24" => "SPORT",
        "Sky Sport Uno" => "SPORT",
        "Sky Sport Uno FHD" => "SPORT",
        "Sky Sport Calcio" => "SPORT",
        "Sky Sport Tennis" => "SPORT",
        "Sky Sport Arena" => "SPORT",
        "Sky Sport Max" => "SPORT",
        "Sky Sport Golf" => "SPORT",
        "Sky Sport F1" => "SPORT",
        "Sky Sport MotoGP" => "SPORT",
        "Sky Sport Basket" => "SPORT",
        "Sky Sport Legend" => "SPORT",
        "Sky Sport Mix" => "SPORT",
        "Sky Sport 251" => "SPORT",
        "Sky Sport 252" => "SPORT",
        "Sky Sport 253" => "SPORT",
        "Sky Sport 254" => "SPORT",
        "Sky Sport 255" => "SPORT",
        "Sky Sport 256" => "SPORT",
        "Sky Sport 257" => "SPORT",
        "Sky Sport 258" => "SPORT",
        "Sky Sport 259" => "SPORT",
        
        // BAMBINI
        "Dea kids" => "BAMBINI",
        "Deakids" => "BAMBINI",
        "Nick Jr" => "BAMBINI",
        "Nickelodeon" => "BAMBINI",
        "Cartoon Network" => "BAMBINI",
        "Boomerang" => "BAMBINI"
    ];

    // MAPPATURA LOGO CANALI
    private const LOGO_MAP = [
        "sky uno" => "https://pixel.disco.nowtv.it/logo/skychb_477_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky atlantic" => "https://pixel.disco.nowtv.it/logo/skychb_226_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky serie" => "https://pixel.disco.nowtv.it/logo/skychb_684_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky investigation" => "https://pixel.disco.nowtv.it/logo/skychb_686_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky collection" => "https://pixel.disco.nowtv.it/logo/skychb_431_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "comedy central" => "https://pixel.disco.nowtv.it/logo/skychb_404_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "mtv" => "https://pixel.disco.nowtv.it/logo/skychb_763_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky tg24" => "https://pixel.disco.nowtv.it/logo/skychb_519_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 24" => "https://pixel.disco.nowtv.it/logo/skychb_35_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport uno" => "https://pixel.disco.nowtv.it/logo/skychb_23_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport calcio" => "https://pixel.disco.nowtv.it/logo/skychb_209_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport tennis" => "https://pixel.disco.nowtv.it/logo/skychb_559_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport arena" => "https://pixel.disco.nowtv.it/logo/skychb_24_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport max" => "https://pixel.disco.nowtv.it/logo/skychb_248_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport golf" => "https://pixel.disco.nowtv.it/logo/skychb_768_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport f1" => "https://pixel.disco.nowtv.it/logo/skychb_478_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport motogp" => "https://pixel.disco.nowtv.it/logo/skychb_483_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport basket" => "https://pixel.disco.nowtv.it/logo/skychb_764_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport legend" => "https://pixel.disco.nowtv.it/logo/skychb_578_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport mix" => "https://pixel.disco.nowtv.it/logo/skychb_579_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 251" => "https://pixel.disco.nowtv.it/logo/skychb_917_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 252" => "https://pixel.disco.nowtv.it/logo/skychb_951_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 253" => "https://pixel.disco.nowtv.it/logo/skychb_233_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 254" => "https://pixel.disco.nowtv.it/logo/skychb_234_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 255" => "https://pixel.disco.nowtv.it/logo/skychb_910_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 256" => "https://pixel.disco.nowtv.it/logo/skychb_912_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 257" => "https://pixel.disco.nowtv.it/logo/skychb_775_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 258" => "https://pixel.disco.nowtv.it/logo/skychb_772_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky sport 259" => "https://pixel.disco.nowtv.it/logo/skychb_613_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema uno" => "https://pixel.disco.nowtv.it/logo/skychb_202_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema due" => "https://pixel.disco.nowtv.it/logo/skychb_564_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema collection" => "https://pixel.disco.nowtv.it/logo/skychb_204_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema family" => "https://pixel.disco.nowtv.it/logo/skychb_255_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema illumination" => "https://pixel.disco.nowtv.it/logo/skychb_255_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema action" => "https://pixel.disco.nowtv.it/logo/skychb_206_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema suspense" => "https://pixel.disco.nowtv.it/logo/skychb_47_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema romance" => "https://pixel.disco.nowtv.it/logo/skychb_231_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema drama" => "https://pixel.disco.nowtv.it/logo/skychb_769_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema comedy" => "https://pixel.disco.nowtv.it/logo/skychb_30_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky cinema stories" => "https://pixel.disco.nowtv.it/logo/skychb_564_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky arte" => "https://pixel.disco.nowtv.it/logo/skychb_74_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky documentaries" => "https://pixel.disco.nowtv.it/logo/skychb_697_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky nature" => "https://pixel.disco.nowtv.it/logo/skychb_695_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky adventure" => "https://pixel.disco.nowtv.it/logo/skychb_961_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "history" => "https://pixel.disco.nowtv.it/logo/skychb_513_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "sky crime" => "https://pixel.disco.nowtv.it/logo/skychb_249_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "deakids" => "https://pixel.disco.nowtv.it/logo/skychb_460_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "nick jr" => "https://pixel.disco.nowtv.it/logo/skychb_424_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "nickelodeon" => "https://pixel.disco.nowtv.it/logo/skychb_320_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "cartoon network" => "https://pixel.disco.nowtv.it/logo/skychb_258_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        "boomerang" => "https://pixel.disco.nowtv.it/logo/skychb_367_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
        
    ];

    public function handle(): void {
        if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
            $this->sendResponse(null, 204, self::CORS_HEADERS);
            return;
        }

        $action = $_GET['action'] ?? null;
        $target = $_GET['url'] ?? null;

        /* ══════════════════════════════════════════════════════════
           GENERA M3U con formato KODIPROP
        ══════════════════════════════════════════════════════════ */
		  // Supporta sia azioni singole che combinate (es. live_mapped)
		$validBaseActions = ['live', 'eventi', 'all', 'mapped'];
		$isValid = false;

		foreach ($validBaseActions as $valid) {
			if ($action === $valid || $action === $valid . '_mapped') {
				$isValid = true;
				break;
			}
		}

		if ($isValid) {
			$this->generateM3u($action, isset($_GET['refresh']));
			return;
}
        
        /* ══════════════════════════════════════════════════════════
           PROXY PER LO STREAM (opzionale, per chi non vuole URL diretti)
        ══════════════════════════════════════════════════════════ */
        if ($action === 'stream' && isset($_GET['url'])) {
            $this->proxyStream(urldecode($_GET['url']));
            return;
        }
        
        /* ══════════════════════════════════════════════════════════
           TEST
        ══════════════════════════════════════════════════════════ */
        if ($action === 'ping') {
            $this->jsonResponse(['ok' => true, 'ts' => time()]);
            return;
        }
        
        if ($target) {
            $this->proxyRequest($target);
            return;
        }
        
        $this->sendHelpPage();
    }

    /**
     * Ottiene la sessione (login e lista canali)
     */
    private function getSession(bool $forceRefresh = false): ?array {
        $session = null;
        
        if (!$forceRefresh && file_exists(self::SESSION_FILE)) {
            $data = json_decode(file_get_contents(self::SESSION_FILE), true);
            if ($data && ($data['expires'] ?? 0) > time()) {
                $session = $data;
            }
        }
        
        if (!$session) {
            $session = $this->doLogin();
            if ($session) {
                $session['expires'] = time() + self::SESSION_TTL;
                file_put_contents(self::SESSION_FILE, json_encode($session));
            }
        }
        
        return $session;
    }

    /**
     * Login a PepperStream
     */
    private function doLogin(): ?array {
        error_log("<!-- Login in corso... -->\n");
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => self::PEPPER_BASE . '/login.php',
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => http_build_query(['password' => self::PEPPER_PASS]),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HEADER => true,
            CURLOPT_USERAGENT => self::UA,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/x-www-form-urlencoded',
                'Referer: ' . self::PEPPER_BASE . '/login.php',
                'Origin: https://pepperstream.xyz',
                'Accept: text/html,application/xhtml+xml,*/*'
            ]
        ]);

        $response = curl_exec($ch);
        curl_close($ch);

        // Estrai cookie
        preg_match_all('/^Set-Cookie:\s*([^;]+)/mi', $response, $matches);
        $cookies = $matches[1] ?? [];
        
        if (empty($cookies)) {
            return null;
        }
        
        $cookieString = implode('; ', $cookies);
        
        // Recupera la lista canali
        $channels = $this->fetchChannels($cookieString);
        if (!$channels) {
            return null;
        }
        
        return [
            'cookie_string' => $cookieString,
            'channels' => $channels
        ];
    }

    /**
     * Recupera la lista canali da regia.php
     */
    private function fetchChannels(string $cookieString): ?array {
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => self::PEPPER_BASE . '/regia.php',
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_USERAGENT => self::UA,
            CURLOPT_HTTPHEADER => [
                'Cookie: ' . $cookieString,
                'Referer: ' . self::PEPPER_BASE . '/regia.php',
                'Accept: text/html,application/xhtml+xml,*/*'
            ]
        ]);

        $html = curl_exec($ch);
        curl_close($ch);

        if (!$html) return null;
        
        // Estrai urlDiretti
        preg_match('/const urlDiretti\s*=\s*({[\s\S]+?});/', $html, $matches);
        if (empty($matches[1])) return null;
        
        preg_match_all('/[\'"]([^\'"]+)[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]/', $matches[1], $pairs);
        
        $channels = [];
        foreach ($pairs[0] as $idx => $match) {
            $name = trim($pairs[1][$idx]);
            $url = str_replace('\\/', '/', $pairs[2][$idx]);
            
            if (str_starts_with($url, 'http')) {
                $channels[] = [
                    'name' => $name,
                    'url' => $url
                ];
            }
        }
        
        return $channels;
    }

    /**
     * Ottiene il gruppo di un canale basato sulla mappatura
     */
    private function getChannelGroup(string $channelName): string {
        // Cerca match esatto
        if (isset(self::CHANNEL_TO_GROUP[$channelName])) {
            return self::CHANNEL_TO_GROUP[$channelName];
        }
        
        // Cerca match case-insensitive
        $channelNameLower = strtolower($channelName);
        foreach (self::CHANNEL_TO_GROUP as $key => $group) {
            if (strtolower($key) === $channelNameLower) {
                return $group;
            }
        }
        
        // Match parziale (es. "Sky Sport Calcio" contiene "Sky Sport")
        foreach (self::CHANNEL_TO_GROUP as $key => $group) {
            if (str_contains($channelNameLower, strtolower($key))) {
                return $group;
            }
        }
        
        // Fallback: cerca per parole chiave
        if (str_contains($channelNameLower, 'sport')) return 'SPORT';
        if (str_contains($channelNameLower, 'cinema')) return 'CINEMA';
        if (str_contains($channelNameLower, 'bambini') || 
            str_contains($channelNameLower, 'cartoon') || 
            str_contains($channelNameLower, 'nick') || 
            str_contains($channelNameLower, 'boomerang') ||
            str_contains($channelNameLower, 'dea kids')) return 'BAMBINI';
        
        return 'INTRATTENIMENTO';
    }

    /**
     * Filtra i canali per action
     */
    private function filterChannels(array $channels, string $action): array {
        if ($action === 'all') {
            return $channels;
        }
        
        if ($action === 'live') {
            // Canali Sky (tutti quelli che iniziano con "Sky" o sono nella mappatura)
            return array_values(array_filter($channels, function($c) {
                $nameLower = strtolower($c['name']);
                return str_starts_with($nameLower, 'sky') || 
                       isset(self::CHANNEL_TO_GROUP[$c['name']]) ||
                       $this->getChannelGroup($c['name']) !== 'SPORT'; // Esclude sport puri
            }));
        }
        
        if ($action === 'eventi') {
            // Solo canali SPORT
            return array_values(array_filter($channels, function($c) {
                return $this->getChannelGroup($c['name']) === 'SPORT';
            }));
        }
        
        return $channels;
    }
	
	/**
	 * Filtra solo i canali presenti in LOGO_MAP
	 */
	private function filterByLogoMap(array $channels): array {
		return array_values(array_filter($channels, function($channel) {
			$nameLower = strtolower($channel['name']);
			
			// Controlla se esiste nella LOGO_MAP
			if (isset(self::LOGO_MAP[$nameLower])) {
				return true;
			}
			
			// Controlla match parziale
			foreach (self::LOGO_MAP as $key => $logo) {
				if (str_contains($nameLower, $key)) {
					return true;
				}
			}
			
			return false;
		}));
	}

    /**
     * Raggruppa i canali per gruppo
     */
    private function groupChannels(array $channels): array {
        $grouped = [];
        foreach ($channels as $channel) {
            $group = $this->getChannelGroup($channel['name']);
            if (!isset($grouped[$group])) {
                $grouped[$group] = [];
            }
            $grouped[$group][] = $channel;
        }
        
        // Ordina i gruppi
        $order = ['CINEMA', 'INTRATTENIMENTO', 'SPORT', 'BAMBINI'];
        uksort($grouped, function($a, $b) use ($order) {
            $posA = array_search($a, $order);
            $posB = array_search($b, $order);
            if ($posA === false && $posB === false) return strcmp($a, $b);
            if ($posA === false) return 1;
            if ($posB === false) return -1;
            return $posA - $posB;
        });
        
        return $grouped;
    }

    /**
     * Estrae la license_key dal parametro ck dell'URL
     * ck è in base64, decodificato = key:kid
     */
    private function extractLicenseKey(string $url): ?string {
        if (preg_match('/[?&]ck=([^&]+)/', $url, $matches)) {
            $ckBase64 = $matches[1];
            $decoded = base64_decode($ckBase64);
            
            if ($decoded !== false && strpos($decoded, ':') !== false) {
                return $decoded;
            }
        }
        return null;
    }

    /**
     * Pulisce l'URL rimuovendo i parametri di licenza
     */
    private function cleanUrl(string $url): string {
        // Rimuovi ck e altri parametri
        $url = preg_replace('/[?&]ck=[^&]*/', '', $url);
        $url = preg_replace('/[?&]c3\.ri=[^&]*/', '', $url);
        $url = preg_replace('/[?&]t=v2/', '', $url);
        
        // Pulisci caratteri superflui
        $url = str_replace('?&', '?', $url);
        $url = rtrim($url, '?');
        $url = rtrim($url, '&');
        
        return $url;
    }

    /**
     * Ottiene il logo del canale dalla mappa
     */
    private function getChannelLogo(string $channelName): string {
        $nameLower = strtolower($channelName);
        
        // Cerca match esatto nella mappa
        if (isset(self::LOGO_MAP[$nameLower])) {
            return self::LOGO_MAP[$nameLower];
        }
        
        // Cerca match parziale (es. "Sky Sport Calcio" -> "sky sport")
        foreach (self::LOGO_MAP as $key => $logo) {
            if (str_contains($nameLower, $key)) {
                return $logo;
            }
        }
        
        // Fallback: genera logo da tvg-id
        $tvgId = $this->getTvgId($channelName);
        return "https://pixel.disco.nowtv.it/logo/{$tvgId}/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT";
    }

/**
 * Genera il file M3U nel formato richiesto
 */
private function generateM3u(string $action, bool $refresh = false): void {
    $session = $this->getSession($refresh);
    
    if (!$session || empty($session['channels'])) {
        $this->sendM3uError('Impossibile ottenere i canali. Riprova.');
        return;
    }
    
    // Determina se dobbiamo filtrare per mappa
    $isMappedFilter = str_ends_with($action, '_mapped');
    $baseAction = $isMappedFilter ? str_replace('_mapped', '', $action) : $action;
    
    // Se l'azione base non è valida, usa 'all'
    if (!in_array($baseAction, ['live', 'eventi', 'all', 'mapped'])) {
        $baseAction = 'all';
    }
    
    // Filtra i canali in base all'azione
    if ($baseAction === 'mapped') {
        $tempChannels = $this->filterChannels($session['channels'], 'all');
        $channels = $this->filterByLogoMap($tempChannels);
    } else {
        $channels = $this->filterChannels($session['channels'], $baseAction);
        
        // Se richiesto, filtra solo canali con logo mappato
        if ($isMappedFilter && $baseAction !== 'mapped') {
            $channels = $this->filterByLogoMap($channels);
        }
    }
    
    $groupedChannels = $this->groupChannels($channels);
    
    // Header M3U
    $m3u = "#EXTM3U\n";
    $m3u .= "# Playlist PepperStream\n";
    $m3u .= "# Action: {$action}\n";
    $m3u .= "# Data: " . date('Y-m-d H:i:s') . "\n";
    $m3u .= "# Nota: I cookie sono validi per " . self::SESSION_TTL . " secondi\n";
    $m3u .= "# Canali totali: " . count($channels) . "\n\n";
    
    foreach ($groupedChannels as $groupName => $groupChannels) {
        $m3u .= "# Playlist {$groupName}\n\n";
        
        foreach ($groupChannels as $channel) {
            $name = $channel['name'];
            $originalUrl = $channel['url'];
            
            // Estrai la license_key dal parametro ck
            $licenseKey = $this->extractLicenseKey($originalUrl);
            
            // Pulisci l'URL (rimuovi ck e parametri)
            $cleanUrl = $this->cleanUrl($originalUrl);
            
            // Metadata del canale
            $tvgId = $this->getTvgId($name);
            $groupTitle = $groupName;
            $tvgLogo = $this->getChannelLogo($name);
            $displayName = $this->formatChannelName($name);
            
            // Riga EXTINF
            $m3u .= "#EXTINF:-1 tvg-id=\"{$tvgId}\" tvg-logo=\"{$tvgLogo}\" group-title=\"{$groupTitle}\",{$displayName}\n";
            
            // Direttive KODIPROP (solo se abbiamo una license_key)
            if ($licenseKey) {
                $m3u .= "#KODIPROP:inputstream.adaptive.manifest_type=mpd\n";
                $m3u .= "#KODIPROP:inputstream.adaptive.license_type=clearkey\n";
                $m3u .= "#KODIPROP:inputstream.adaptive.license_key={$licenseKey}\n";
            }
            
            // URL pulito
            $m3u .= "{$cleanUrl}\n\n";
        }
    }
    
    // Headers per il download
    $headers = array_merge(self::CORS_HEADERS, [
        'Content-Type' => 'application/vnd.apple.mpegurl',
        'Content-Disposition' => 'attachment; filename="pepper_' . $action . '.m3u"',
        'Cache-Control' => 'no-cache'
    ]);
    
    $this->sendResponse($m3u, 200, $headers);
}

    /**
     * Proxy per lo stream (se non vuoi URL diretti)
     */
    private function proxyStream(string $url): void {
        $session = $this->getSession();
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => false,
            CURLOPT_HEADER => false,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_USERAGENT => self::UA,
            CURLOPT_HTTPHEADER => [
                'Cookie: ' . ($session['cookie_string'] ?? ''),
                'Referer: ' . self::PEPPER_BASE . '/regia.php'
            ],
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_WRITEFUNCTION => function($curl, $data) {
                echo $data;
                ob_flush();
                flush();
                return strlen($data);
            }
        ]);
        
        if (str_contains($url, '.mpd')) {
            header('Content-Type: application/dash+xml');
        } elseif (str_contains($url, '.m3u8')) {
            header('Content-Type: application/vnd.apple.mpegurl');
        }
        
        header('Access-Control-Allow-Origin: *');
        header('Cache-Control: no-cache');
        
        curl_exec($ch);
        curl_close($ch);
    }

    /**
     * Helper: tvg-id
     */
    private function getTvgId(string $name): string {
        $map = [
            # Sky Cinema
        "sky cinema illumination" => "sky.cinema.family.it",
        "sky cinema collection"   => "sky.cinema.collection.it",
        "sky cinema suspense"     => "sky.cinema.suspense.it",
        "sky cinema romance"      => "sky.cinema.romance.it",
        "sky cinema stories"      => "sky.cinema.due.it",
        "sky cinema comedy"       => "sky.cinema.comedy.it",
        "sky cinema action"       => "sky.cinema.action.it",
        "sky cinema family"       => "sky.cinema.family.it",
        "sky cinema drama"        => "sky.cinema.drama.it",
        "sky cinema uno"          => "sky.cinema.uno.it",
        "sky cinema due"          => "sky.cinema.due.it",
        # Sky Sport
        "sky sport calcio"        => "sky.sport.calcio.it",
        "sky sport tennis"        => "sky.sport.tennis.it",
        "sky sport motogp"        => "sky.sport.motogp.it",
        "sky sport basket"        => "sky.sport.basket.it",
        "sky sport legend"        => "sky.sport.legend.it",
        "sky sport arena"         => "sky.sport.arena.it",
        "sky sport golf"          => "sky.sport.golf.it",
        "sky sport mix"           => "sky.sport.mix.it",
        "sky sport max"           => "sky.sport.max.it",
        "sky sport uno"           => "sky.sport1.it",
        "sky sport f1"            => "sky.sport.f1.it",
        "sky sport 24"            => "sky.sport24.it",
        "sky sport 251"           => "sky.sport.251.it",
        "sky sport 252"           => "sky.sport.252.it",
        "sky sport 253"           => "sky.sport.253.it",
        "sky sport 254"           => "sky.sport.254.it",
        "sky sport 255"           => "sky.sport.255.it",
        "sky sport 256"           => "sky.sport.256.it",
        "sky sport 257"           => "sky.sport.257.it",
        "sky sport 258"           => "sky.sport.258.it",
        "sky sport 259"           => "sky.sport.259.it",
        # Sky altri
        "sky investigation"       => "sky.investigation.it",
        "sky documentaries"       => "sky.documentaries.it",
        "sky collection"          => "sky.collection.it",
        "sky adventure"           => "sky.adventure.it",
        "sky atlantic"            => "sky.atlantic.it",
        "sky nature"              => "sky.nature.it",
        "sky crime"               => "sky.crime.it",
        "sky serie"               => "sky.serie.it",
        "sky arte"                => "sky.arte.it",
        "sky tg24"                => "sky.tg24.it",
        "sky uno"                 => "sky.uno.it",
        # Altri canali
        "comedy central"          => "comedycentral.it",
        "cartoon network"         => "cartoonnetwork.it",
        "nickelodeon"             => "nickelodeon.it",
        "boomerang"               => "boomerang.it",
        "nick jr"                 => "nickjr.it",
        "deakids"                 => "deakids.it",
        "history"                 => "history.it",
        "mtv"                     => "mtv.it",
        ];
        
        $nameLower = strtolower($name);
        foreach ($map as $key => $id) {
            if (str_contains($nameLower, $key)) {
                return $id;
            }
        }
        return preg_replace('/[^a-zA-Z0-9]/', '', $name) . '.it';
    }

    private function renameChannel(string $name): string {
    $renames = [
        'Sky Cinema Illumination' => 'Sky Cinema Family',
    ];
    return $renames[$name] ?? $name;
}

    /**
     * Helper: format channel name
     */
	   private function formatChannelName(string $name): string {
		$name = $this->renameChannel($name);
		return ucwords(strtolower($name));
	}
    

    /**
     * Invia errore in formato M3U
     */
    private function sendM3uError(string $message): void {
        $m3u = "#EXTM3U\n";
        $m3u .= "#EXTINF:-1,❌ ERRORE: {$message}\n";
        $m3u .= "https://httpbin.org/status/503\n";
        
        $this->sendResponse($m3u, 200, [
            'Content-Type' => 'application/vnd.apple.mpegurl',
            'Access-Control-Allow-Origin' => '*'
        ]);
    }

    /**
     * Proxy generico
     */
    private function proxyRequest(string $target): void {
        $ch = curl_init($target);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_USERAGENT, self::UA);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
        curl_close($ch);
        
        header('Access-Control-Allow-Origin: *');
        if ($contentType) header('Content-Type: ' . $contentType);
        http_response_code($httpCode);
        echo $response;
    }

    /**
     * Risposta JSON
     */
    private function jsonResponse(array $data, int $status = 200): void {
        http_response_code($status);
        header('Content-Type: application/json');
        header('Access-Control-Allow-Origin: *');
        echo json_encode($data);
        exit;
    }

    /**
     * Pagina help
     */
    private function sendHelpPage(): void {
        $baseUrl = (isset($_SERVER['HTTPS']) ? 'https' : 'http') . '://' . $_SERVER['HTTP_HOST'] . $_SERVER['SCRIPT_NAME'];
        echo <<<HTML
        <!DOCTYPE html>
        <html>
        <head><title>PepperStream M3U Generator</title><meta charset="UTF-8"></head>
        <body style="font-family:monospace;padding:20px;max-width:800px">
            <h1>📺 PepperStream M3U Generator</h1>
            <p>Genera playlist M3U con formato KODIPROP per Kodi/OTT</p>
            
            <h2>📡 URL Playlist:</h2>
            <ul>
                <li><a href="{$baseUrl}?action=all">{$baseUrl}?action=all</a> - Tutti i canali (raggruppati)</li>
                <li><a href="{$baseUrl}?action=live">{$baseUrl}?action=live</a> - Canali Sky (escluso sport)</li>
                <li><a href="{$baseUrl}?action=eventi">{$baseUrl}?action=eventi</a> - Solo Sport/Eventi</li>
				
				<li><a href="{$baseUrl}?action=mapped">{$baseUrl}?action=mapped</a> - Solo canali con logo mappato</li>
				<li><a href="{$baseUrl}?action=live_mapped">{$baseUrl}?action=live_mapped</a> - Live con logo mappato</li>
				<li><a href="{$baseUrl}?action=eventi_mapped">{$baseUrl}?action=eventi_mapped</a> - Sport con logo mappato</li>
            </ul>
            
            <h2>📋 Gruppi disponibili:</h2>
            <ul>
                <li><strong>CINEMA</strong> - Sky Cinema e varianti</li>
                <li><strong>INTRATTENIMENTO</strong> - Sky Uno, Atlantic, Serie, Comedy, MTV, ecc.</li>
                <li><strong>SPORT</strong> - Sky Sport, Calcio, F1, MotoGP, ecc.</li>
                <li><strong>BAMBINI</strong> - Cartoon Network, Nickelodeon, Boomerang, ecc.</li>
            </ul>
            
            <h2>📋 Formato output:</h2>
            <pre style="background:#f0f0f0;padding:10px">
# Playlist CINEMA

#EXTINF:-1 tvg-id="SkyCinemaUno.it" tvg-logo="..." group-title="CINEMA",Sky Cinema Uno
#KODIPROP:inputstream.adaptive.manifest_type=mpd
#KODIPROP:inputstream.adaptive.license_type=clearkey
#KODIPROP:inputstream.adaptive.license_key=1118a48358c744f5075ddd54441c9207:c0cd1f001bba58b1261d12ff04e4d5bd
https://.../master.mpd
            </pre>
            
            <p><strong>💡 Uso in Kodi:</strong> Aggiungi URL playlist come sorgente M3U</p>
            <p><small>Sessione valida 1 ora. Usa <code>&refresh=1</code> per forzare refresh</small></p>
        </body>
        </html>
HTML;
    }

    /**
     * Invia risposta
     */
    private function sendResponse(?string $body, int $status = 200, array $headers = []): void {
        http_response_code($status);
        foreach ($headers as $name => $value) {
            header("{$name}: {$value}");
        }
        if ($body !== null) {
            echo $body;
        }
        exit;
    }
}

// Helper per PHP < 8
if (!function_exists('str_contains')) {
    function str_contains($haystack, $needle) { return $needle !== '' && strpos($haystack, $needle) !== false; }
}
if (!function_exists('str_starts_with')) {
    function str_starts_with($haystack, $needle) { return $needle !== '' && strncmp($haystack, $needle, strlen($needle)) === 0; }
}
if (!function_exists('str_ends_with')) {
    function str_ends_with($haystack, $needle) {
        return $needle !== '' && substr($haystack, -strlen($needle)) === $needle;
    }
}
// Esecuzione
$proxy = new PepperProxy();
$proxy->handle();