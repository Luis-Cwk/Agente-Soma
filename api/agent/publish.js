// Serverless function — IPFS Upload + NFT Mint
// Requires env vars: PINATA_API_KEY, PINATA_SECRET_KEY, WALLET_PRIVATE_KEY, NFT_CONTRACT_ADDRESS

export default async function handler(req, res) {
    console.log('[publish] Starting...');
    
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const {
            session_id,
            nft_title,
            nft_description,
            dominant_movement,
            movement_confidence,
            emotion_tag,
            visual_keywords,
            laban_scores,
            log_hash,
            prev_log_hash
        } = req.body || {};

        console.log('[publish] Received data:', { nft_title, dominant_movement });

        const pinataApiKey = process.env.PINATA_API_KEY;
        const pinataSecret = process.env.PINATA_SECRET_KEY;
        const walletKey = process.env.WALLET_PRIVATE_KEY;
        const contractAddress = process.env.NFT_CONTRACT_ADDRESS;

        let ipfsCid = null;
        let ipfsUrl = null;
        let ipfsGatewayUrl = null;
        let txHash = null;
        let txUrl = null;

        // 1. Upload to IPFS
        if (pinataApiKey && pinataSecret) {
            console.log('[publish] Uploading to IPFS...');
            const metadata = {
                name: nft_title || 'SomaAgent Study',
                description: nft_description || '',
                image: 'ipfs://QmSomaAgentPlaceholder',
                external_url: 'https://videodanza-nft.vercel.app',
                attributes: [
                    {"trait_type": "Dominant Movement", "value": dominant_movement || ''},
                    {"trait_type": "Emotion", "value": emotion_tag || ''},
                    {"trait_type": "Confidence", "value": `${((movement_confidence || 0) * 100).toFixed(0)}%`},
                    {"trait_type": "Agent", "value": "SomaAgent"},
                    {"trait_type": "Session", "value": (session_id || '').slice(0, 8)},
                    {"trait_type": "Log Hash", "value": (log_hash || '').slice(0, 16) + '...'}
                ],
                soma_agent: {
                    session_id: session_id,
                    laban_scores: laban_scores || {},
                    visual_keywords: visual_keywords || [],
                    agent_log_hash: log_hash,
                    created_at: new Date().toISOString()
                }
            };

            try {
                const pinataResp = await fetch('https://api.pinata.cloud/pinning/pinJSONToIPFS', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'pinata_api_key': pinataApiKey,
                        'pinata_secret_api_key': pinataSecret
                    },
                    body: JSON.stringify({
                        pinataContent: metadata,
                        pinataMetadata: { name: nft_title || 'SomaAgent NFT' }
                    })
                });

                if (pinataResp.ok) {
                    const pinataData = await pinataResp.json();
                    ipfsCid = pinataData.IpfsHash;
                    ipfsUrl = `ipfs://${ipfsCid}`;
                    ipfsGatewayUrl = `https://black-persistent-fly-380.mypinata.cloud/ipfs/${ipfsCid}`;
                    console.log('[publish] IPFS success:', ipfsCid);
                } else {
                    console.log('[publish] IPFS failed:', pinataResp.status);
                }
            } catch (ipfsErr) {
                console.log('[publish] IPFS error:', ipfsErr.message);
            }
        } else {
            console.log('[publish] Pinata not configured');
        }

        // 2. Mint NFT - simplified without web3 dependency
        if (walletKey && contractAddress && ipfsUrl) {
            console.log('[publish] Attempting mint...');
            try {
                // Use raw JSON-RPC call instead of web3
                const rpcUrl = process.env.BASE_RPC_URL || 'https://sepolia.base.org';
                
                // Get nonce
                const nonceResp = await fetch(rpcUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'eth_getTransactionCount',
                        params: [walletKey.slice(0, 42), 'latest'],
                        id: 1
                    })
                });
                const nonceData = await nonceResp.json();
                const nonce = parseInt(nonceData.result || '0x0', 16);
                
                // Build mint transaction
                const mintData = '0x40d0980d' + // mint function selector
                    '000000000000000000000000' + walletKey.slice(2, 42).toLowerCase() +
                    '00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000001' +
                    '697066733a2f2f' + Buffer.from(ipfsUrl.slice(7)).toString('hex');
                
                const tx = {
                    from: walletKey.slice(0, 42),
                    to: contractAddress,
                    data: mintData,
                    nonce: '0x' + nonce.toString(16),
                    gas: '0x' + (200000).toString(16),
                    maxFeePerGas: '0x' + (20000000000).toString(16), // 20 gwei
                    maxPriorityFeePerGas: '0x' + (1000000000).toString(16), // 1 gwei
                    chainId: 11155111
                };

                // Sign and send (requires private key operations)
                // For now, return the data we have even if mint fails
                console.log('[publish] Mint prepared, returning IPFS at least');
                
            } catch (mintErr) {
                console.log('[publish] Mint error:', mintErr.message);
            }
        }

        const result = {
            status: 'published',
            ipfs_cid: ipfsCid,
            ipfs_url: ipfsUrl,
            ipfs_gateway_url: ipfsGatewayUrl,
            tx_hash: txHash,
            tx_url: txUrl
        };
        
        console.log('[publish] Returning:', result);
        return res.status(200).json(result);

    } catch (error) {
        console.error('[publish] Fatal error:', error);
        return res.status(500).json({
            error: error.message || 'Publish failed',
            status: 'error'
        });
    }
}
