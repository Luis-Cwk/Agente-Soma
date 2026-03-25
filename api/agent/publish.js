// Serverless function — IPFS Upload + NFT Mint
// Requires env vars: PINATA_API_KEY, PINATA_SECRET_KEY, WALLET_PRIVATE_KEY, NFT_CONTRACT_ADDRESS

import crypto from 'crypto';

const MINT_ABI = [
    {
        "name": "mint",
        "type": "function",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenURI", "type": "string"}
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "stateMutability": "nonpayable"
    }
];

export default async function handler(req, res) {
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

        const pinataApiKey = process.env.PINATA_API_KEY;
        const pinataSecret = process.env.PINATA_SECRET_KEY;
        const walletKey = process.env.WALLET_PRIVATE_KEY;
        const contractAddress = process.env.NFT_CONTRACT_ADDRESS;
        const baseRpcUrl = process.env.BASE_RPC_URL || 'https://sepolia.base.org';

        let ipfsCid = null;
        let ipfsUrl = null;
        let txHash = null;
        let txUrl = null;

        // 1. Upload to IPFS
        if (pinataApiKey && pinataSecret) {
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
            }
        }

        // 2. Mint NFT on Sepolia
        if (walletKey && contractAddress && ipfsUrl) {
            const { Web3 } = await import('web3');
            const web3 = new Web3(baseRpcUrl);

            try {
                const account = web3.eth.accounts.privateKeyToAccount(walletKey);
                const nonce = await web3.eth.getTransactionCount(account.address);

                const contract = new web3.eth.Contract(MINT_ABI, contractAddress);
                const tx = contract.methods.mint(account.address, ipfsUrl).send({
                    from: account.address,
                    nonce: nonce,
                    gas: 200000,
                    maxFeePerGas: web3.utils.toWei('20', 'gwei'),
                    maxPriorityFeePerGas: web3.utils.toWei('1', 'gwei'),
                    chainId: 11155111 // Sepolia
                });

                txHash = tx.transactionHash;
                txUrl = `https://sepolia.etherscan.io/tx/${txHash}`;
            } catch (mintErr) {
                console.error('Mint error:', mintErr);
            }
        }

        // Build gateway URL
        const ipfsGatewayUrl = ipfsCid
            ? `https://black-persistent-fly-380.mypinata.cloud/ipfs/${ipfsCid}`
            : null;

        return res.status(200).json({
            status: 'published',
            ipfs_cid: ipfsCid,
            ipfs_url: ipfsUrl,
            ipfs_gateway_url: ipfsGatewayUrl,
            tx_hash: txHash,
            tx_url: txUrl
        });

    } catch (error) {
        console.error('Publish error:', error);
        return res.status(500).json({
            error: error.message || 'Publish failed',
            status: 'error'
        });
    }
}
